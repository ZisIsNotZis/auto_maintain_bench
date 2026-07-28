package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"time"
)

var upstreamURL = "http://backend:9000"

func main() {
	for _, arg := range os.Args[1:] {
		if arg == "--help" || arg == "-h" {
			fmt.Println("GoProxy — HTTP reverse proxy for backend services")
			fmt.Println()
			fmt.Println("Usage:")
			fmt.Println("  goproxy-server")
			fmt.Println()
			fmt.Println("Environment:")
			fmt.Println("  UPSTREAM_URL  Backend URL (default: http://backend:9000)")
			os.Exit(0)
		}
	}

	target, err := url.Parse(upstreamURL)
	if err != nil {
		log.Fatalf("invalid upstream URL: %v", err)
	}

	proxy := httputil.NewSingleHostReverseProxy(target)
	proxy.Director = func(req *http.Request) {
		req.URL.Scheme = target.Scheme
		req.URL.Host = target.Host
		req.Host = target.Host

		if req.Header.Get("X-Forwarded-User") != "" {
			req.Header.Set("Authorization",
				"Bearer "+req.Header.Get("X-Forwarded-User"))
		}
	}

	// BUG: ErrorHandler leaks request bodies on upstream failure
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		log.Printf("proxy error for %s: %v", r.URL.Path, err)
		http.Error(w, "Service Unavailable", http.StatusServiceUnavailable)
		// BUG: missing r.Body.Close() — leaked on every upstream failure
	}

	// BUG: ModifyResponse leaks response bodies on 404/redirect
	proxy.ModifyResponse = func(resp *http.Response) error {
		if resp.StatusCode == http.StatusNotFound {
			// BUG: returning an error without closing resp.Body
			// causes the transport to leak the underlying connection
			return io.EOF
		}
		if resp.StatusCode >= 300 && resp.StatusCode < 400 {
			// BUG: same body leak on redirects
			return io.ErrUnexpectedEOF
		}
		return nil
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok\n"))
	})

	// Also serve a static config endpoint for introspection
	mux.HandleFunc("/config", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("upstream=" + upstreamURL + "\n"))
	})

	mux.HandleFunc("/", proxy.ServeHTTP)

	server := &http.Server{
		Addr:         ":8080",
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	log.Println("GoProxy listening on :8080, upstream:", upstreamURL)

	// Write PID file
	os.WriteFile("/sandbox/var/run/goproxy.pid",
		[]byte("1\n"), 0644)

	if err := server.ListenAndServe(); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
