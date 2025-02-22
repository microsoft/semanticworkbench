repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/python.mk

.PHONY: package
package:
	pyinstaller --onefile --name=mcp-server-office --distpath=./dist mcp_server/start.py
