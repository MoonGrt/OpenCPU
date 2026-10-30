; Byte-oriented freestanding memory operations, OpenCPU LLVM ABI v2.
target triple = "opencpu-unknown-none"
target datalayout = "e-m:e-p:16:16-i32:16-i64:16-f32:16-f64:16-n16-S16"

define ptr @memcpy(ptr %dst, ptr %src, i16 %size) #0 {
entry:
  br label %loop
loop:
  %i = phi i16 [ 0, %entry ], [ %next, %copy ]
  %done = icmp eq i16 %i, %size
  br i1 %done, label %exit, label %copy
copy:
  %s = getelementptr i8, ptr %src, i16 %i
  %d = getelementptr i8, ptr %dst, i16 %i
  %byte = load i8, ptr %s, align 1
  store i8 %byte, ptr %d, align 1
  %next = add i16 %i, 1
  br label %loop
exit:
  ret ptr %dst
}

define ptr @memmove(ptr %dst, ptr %src, i16 %size) #0 {
entry:
  %forward = icmp ult ptr %dst, %src
  br i1 %forward, label %forwards, label %backwards
forwards:
  %result = call ptr @memcpy(ptr %dst, ptr %src, i16 %size)
  ret ptr %result
backwards:
  br label %loop
loop:
  %i = phi i16 [ %size, %backwards ], [ %previous, %copy ]
  %done = icmp eq i16 %i, 0
  br i1 %done, label %exit, label %copy
copy:
  %previous = sub i16 %i, 1
  %s = getelementptr i8, ptr %src, i16 %previous
  %d = getelementptr i8, ptr %dst, i16 %previous
  %byte = load i8, ptr %s, align 1
  store i8 %byte, ptr %d, align 1
  br label %loop
exit:
  ret ptr %dst
}

define ptr @memset(ptr %dst, i16 %value, i16 %size) #0 {
entry:
  %byte = trunc i16 %value to i8
  br label %loop
loop:
  %i = phi i16 [ 0, %entry ], [ %next, %fill ]
  %done = icmp eq i16 %i, %size
  br i1 %done, label %exit, label %fill
fill:
  %d = getelementptr i8, ptr %dst, i16 %i
  store i8 %byte, ptr %d, align 1
  %next = add i16 %i, 1
  br label %loop
exit:
  ret ptr %dst
}

define i16 @memcmp(ptr %left, ptr %right, i16 %size) #0 {
entry:
  br label %loop
loop:
  %i = phi i16 [ 0, %entry ], [ %next, %equal ]
  %done = icmp eq i16 %i, %size
  br i1 %done, label %same, label %compare
compare:
  %l = getelementptr i8, ptr %left, i16 %i
  %r = getelementptr i8, ptr %right, i16 %i
  %a = load i8, ptr %l, align 1
  %b = load i8, ptr %r, align 1
  %eq = icmp eq i8 %a, %b
  br i1 %eq, label %equal, label %different
equal:
  %next = add i16 %i, 1
  br label %loop
different:
  %aa = zext i8 %a to i16
  %bb = zext i8 %b to i16
  %delta = sub i16 %aa, %bb
  ret i16 %delta
same:
  ret i16 0
}

attributes #0 = { nounwind "opencpu-runtime" }
