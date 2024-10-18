# posix shell
rm = rm -rf
fix_path = $(1)
touch = touch $(1)
true_expression = true
stdout_redirect_null = 1>/dev/null
stderr_redirect_null = 2>/dev/null
stderr_redirect_stdout = 2>&1

# windows shell
ifeq ($(suffix $(SHELL)),.exe)
rm = rd /S /Q
fix_path = $(subst /,\,$(abspath $(1)))
# https://ss64.com/nt/touch.html
touch = type nul >> $(call fix_path,$(1)) && copy /y /b $(call fix_path,$(1))+,, $(call fix_path,$(1))
true_expression = VER>NUL
stdout_redirect_null = 1>NUL
stderr_redirect_null = 2>NUL
stderr_redirect_stdout = 2>&1
endif
