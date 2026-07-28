all: goproxy-server

goproxy-server: main.go go.mod
	go build -o goproxy-server .

clean:
	rm -f goproxy-server

.PHONY: all clean
