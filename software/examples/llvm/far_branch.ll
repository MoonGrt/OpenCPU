; Expected a1 = 32771; the conditional skips a long arithmetic block.
define i16 @long_branch(i16 %x) {
entry:
  %zero = icmp eq i16 %x, 0
  br i1 %zero, label %short, label %long
long:
  %m0 = mul i16 %x, 3
  %v0 = xor i16 %m0, 12345
  %m1 = mul i16 %v0, 3
  %v1 = xor i16 %m1, 12345
  %m2 = mul i16 %v1, 3
  %v2 = xor i16 %m2, 12345
  %m3 = mul i16 %v2, 3
  %v3 = xor i16 %m3, 12345
  %m4 = mul i16 %v3, 3
  %v4 = xor i16 %m4, 12345
  %m5 = mul i16 %v4, 3
  %v5 = xor i16 %m5, 12345
  %m6 = mul i16 %v5, 3
  %v6 = xor i16 %m6, 12345
  %m7 = mul i16 %v6, 3
  %v7 = xor i16 %m7, 12345
  %m8 = mul i16 %v7, 3
  %v8 = xor i16 %m8, 12345
  %m9 = mul i16 %v8, 3
  %v9 = xor i16 %m9, 12345
  %m10 = mul i16 %v9, 3
  %v10 = xor i16 %m10, 12345
  %m11 = mul i16 %v10, 3
  %v11 = xor i16 %m11, 12345
  %m12 = mul i16 %v11, 3
  %v12 = xor i16 %m12, 12345
  %m13 = mul i16 %v12, 3
  %v13 = xor i16 %m13, 12345
  %m14 = mul i16 %v13, 3
  %v14 = xor i16 %m14, 12345
  %m15 = mul i16 %v14, 3
  %v15 = xor i16 %m15, 12345
  %m16 = mul i16 %v15, 3
  %v16 = xor i16 %m16, 12345
  %m17 = mul i16 %v16, 3
  %v17 = xor i16 %m17, 12345
  %m18 = mul i16 %v17, 3
  %v18 = xor i16 %m18, 12345
  %m19 = mul i16 %v18, 3
  %v19 = xor i16 %m19, 12345
  %m20 = mul i16 %v19, 3
  %v20 = xor i16 %m20, 12345
  %m21 = mul i16 %v20, 3
  %v21 = xor i16 %m21, 12345
  %m22 = mul i16 %v21, 3
  %v22 = xor i16 %m22, 12345
  %m23 = mul i16 %v22, 3
  %v23 = xor i16 %m23, 12345
  ret i16 %v23
short:
  ret i16 42
}
define i16 @main() {
  %a = call i16 @long_branch(i16 1)
  %b = call i16 @long_branch(i16 0)
  %result = add i16 %a, %b
  ret i16 %result
}
