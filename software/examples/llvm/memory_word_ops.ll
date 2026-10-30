; Expected a1 = 52651 (0xcdab); all physical accesses must remain 16-bit words.
define i16 @touch_word() {
  ret i16 0
}
define i16 @main() {
entry:
  %slot = alloca i16, align 2
  store volatile i16 43981, ptr %slot, align 2
  %ignored = call i16 @touch_word()
  %high_word = load volatile i16, ptr %slot, align 2
  %shifted = lshr i16 %high_word, 8
  %high = and i16 %shifted, 255
  %low_word = load volatile i16, ptr %slot, align 2
  %low = and i16 %low_word, 255
  %positioned = shl i16 %low, 8
  %result = or i16 %positioned, %high
  ret i16 %result
}
