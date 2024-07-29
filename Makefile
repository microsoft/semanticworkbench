# Runs make in all subdirectories with a Makefile, passing the make target to each.
# Directories are make'ed in top down order.
# ex: make (runs DEFAULT_GOAL)
# ex: make clean (runs clean)
# ex: make install (runs install)

.DEFAULT_GOAL := install

# You can pass in a list of files or directories to retain when running `clean/git-clean`
# ex: make clean GIT_CLEAN_RETAIN=".env .data"
# As always with make, you can also set this as an environment variable
GIT_CLEAN_RETAIN ?= .env
GIT_CLEAN_EXCLUDE = $(foreach v,$(GIT_CLEAN_RETAIN),--exclude !$(v))

.PHONY: git-clean
git-clean:
	git clean -dffX . $(GIT_CLEAN_EXCLUDE)

include ./build-tools/makefiles/shell.mk

FILTER_OUT = $(foreach v,$(2),$(if $(findstring $(1),$(v)),,$(v)))
MAKE_FILES = $(shell find . -name Makefile -mindepth 2)
ALL_MAKE_DIRS = $(filter-out ./,$(dir $(MAKE_FILES)))
ifeq ($(suffix $(SHELL)),.exe)
MAKE_FILES = $(shell dir Makefile /b /s)
ALL_MAKE_DIRS = $(filter-out $(subst /,\,$(abspath ./)),$(patsubst %\,%,$(dir $(MAKE_FILES))))
endif

MAKE_DIRS := $(call FILTER_OUT,site-packages,$(call FILTER_OUT,node_modules,$(sort $(ALL_MAKE_DIRS))))

.PHONY: clean install test format lint $(MAKE_DIRS)
clean: git-clean
clean install test format lint: $(MAKE_DIRS)

$(MAKE_DIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS) || $(true_expression)
