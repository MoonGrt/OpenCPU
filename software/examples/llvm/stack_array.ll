; Expected a1 = 666; accesses across a 40-word frame need word/byte conversion.
define i16 @touch() {
  ret i16 1
}
define i16 @main() {
entry:
  %array = alloca [40 x i16], align 2
  %first = getelementptr [40 x i16], ptr %array, i32 0, i32 0
  %middle = getelementptr [40 x i16], ptr %array, i32 0, i32 17
  %last = getelementptr [40 x i16], ptr %array, i32 0, i32 39
  store i16 111, ptr %first, align 2
  store i16 222, ptr %middle, align 2
  store i16 333, ptr %last, align 2
  %ignored = call i16 @touch()
  %a = load i16, ptr %first, align 2
  %b = load i16, ptr %middle, align 2
  %c = load i16, ptr %last, align 2
  %ab = add i16 %a, %b
  %result = add i16 %ab, %c
  ret i16 %result
}
