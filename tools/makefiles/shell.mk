rm = rm -rf
fix_path = $(1)
touch = touch $(1)
true_expression = true
null_stderr = 2>/dev/null


ifeq ($(OS),Windows_NT)
rm = rd /S /Q
fix_path = $(subst /,\,$(abspath $(1)))
# https://ss64.com/nt/touch.html
touch = type nul >> $(call fix_path,$(1)) && copy /y /b $(call fix_path,$(1))+,, $(call fix_path,$(1))
true_expression = VER>NUL
null_stderr = 2>NUL
endif
