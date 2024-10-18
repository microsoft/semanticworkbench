# Runs make in all recursive subdirectories with a Makefile, passing the make target to each.
# Directories are make'ed in top down order.
# ex: make (runs DEFAULT_GOAL)
# ex: make clean (runs clean)
# ex: make install (runs install)
mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

.DEFAULT_GOAL := install

# You can pass in a list of files or directories to retain when running `clean/git-clean`
# ex: make clean GIT_CLEAN_RETAIN=".env .data"
# As always with make, you can also set this as an environment variable
GIT_CLEAN_RETAIN ?= .env
GIT_CLEAN_EXCLUDE = $(foreach v,$(GIT_CLEAN_RETAIN),--exclude !$(v))

.PHONY: git-clean
git-clean:
	git clean -dffX . $(GIT_CLEAN_EXCLUDE)

FILTER_OUT = $(foreach v,$(2),$(if $(findstring $(1),$(v)),,$(v)))
MAKE_FILES = $(shell find . -mindepth 2 -name Makefile)
ALL_MAKE_DIRS = $(sort $(filter-out ./,$(dir $(MAKE_FILES))))
ifeq ($(suffix $(SHELL)),.exe)
MAKE_FILES = $(shell dir Makefile /b /s)
ALL_MAKE_DIRS = $(sort $(filter-out $(subst /,\,$(abspath ./)),$(patsubst %\,%,$(dir $(MAKE_FILES)))))
endif

MAKE_DIRS := $(call FILTER_OUT,site-packages,$(call FILTER_OUT,node_modules,$(ALL_MAKE_DIRS)))

ifndef IS_RECURSIVE_MAKE

.PHONY: .clean-error-log .print-error-log

MAKE_CMD_MESSAGE = $(if $(MAKECMDGOALS), $(MAKECMDGOALS),)

.clean-error-log:
	@$(rm) $(mkfile_dir)/.make_error_dirs $(stdout_redirect_null) $(stderr_redirect_stdout) || $(true_expression)

.print-error-log:
	@if [ -s $(call fix_path,$(mkfile_dir)/.make_error_dirs) ]; then \
		echo "\n\033[31;1mDirectories failed to make$(MAKE_CMD_MESSAGE):\033[0m\n"; \
		cat $(call fix_path,$(mkfile_dir)/.make_error_dirs); \
		echo ""; \
		$(rm) $(call fix_path,$(mkfile_dir)/.make_error_log) $(stdout_redirect_null) $(stderr_redirect_stdout) || $(true_expression); \
		$(rm) $(call fix_path,$(mkfile_dir)/.make_error_dirs) $(stdout_redirect_null) $(stderr_redirect_stdout) || $(true_expression); \
		exit 1; \
	fi

.PHONY: clean install test format lint $(MAKE_DIRS)

clean: git-clean

clean install test format lint: .clean-error-log $(MAKE_DIRS) .print-error-log

endif

VERBOSE ?= 0

$(MAKE_DIRS):
ifdef FAIL_ON_ERROR
	$(MAKE) -C $@ $(MAKECMDGOALS) IS_RECURSIVE_MAKE=1
else
	@$(rm) $@.make_log
	@echo $(MAKE) -C $@ $(MAKECMDGOALS)
	@$(MAKE) -C $@ $(MAKECMDGOALS) IS_RECURSIVE_MAKE=1 1>$(call fix_path,$@.make_log) $(stderr_redirect_stdout) || \
		( \
			grep -qF 'No rule to make target' $(call fix_path,$@.make_log) || ( \
				touch $@.make_error; \
				echo "\t$@" >> $(call fix_path,$(mkfile_dir)/.make_error_dirs); \
			) \
		)
	@if [ -e $@.make_error ]; then \
		echo "\n\033[31;1mmake -C $@$(MAKE_CMD_MESSAGE) failed:\033[0m\n" ; \
	fi
	@if [ "$(VERBOSE)" != "0" -o -e $@.make_error ]; then \
		cat $(call fix_path,$@.make_log); \
	fi
	@$(rm) $@.make_log
	@$(rm) $@.make_error
endif

include $(mkfile_dir)/shell.mk
