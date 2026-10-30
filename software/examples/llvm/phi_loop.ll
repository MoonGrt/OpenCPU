; Expected a1 = 45, the sum of 0 through 9.
define i16 @main() {
entry:
  br label %loop
loop:
  %index = phi i16 [ 0, %entry ], [ %next, %body ]
  %sum = phi i16 [ 0, %entry ], [ %updated, %body ]
  %more = icmp ult i16 %index, 10
  br i1 %more, label %body, label %done
body:
  %updated = add i16 %sum, %index
  %next = add i16 %index, 1
  br label %loop
done:
  ret i16 %sum
}
