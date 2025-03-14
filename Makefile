this_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
include $(this_dir)/tools/makefiles/recursive.mk
