`rune`-based PanCJKV IVD Collection support
=============

[PanCJKV IVD Collection](https://github.com/adobe-type-tools/pancjkv-ivd-collection/) is an unregistered IVD collection,
that makes use of Unicode Variation Selectors to distinguish CJK ideograph glyphs on a per-region basis.

This crate add support for PanCJKV IVD Collection support to `rune`-based iterators, by allowing unannotated CJK ideograph abstract characters be transformed into annotated form explicitly.


## Example

```rust
use runestr::{rune, RuneString};
use runestr_pancjkv::{PanCJKVAnnotate, PanCJKVRegion}

fn main() {
    let test = RuneString::from_str_lossy("\u{6211}\u{030C}\u{4EEC}\u{E01EE}\u{0301}");
    assert_eq!(2, test.runes().count());
    let result = test
        .runes()
        .annotate_with_pan_cjkv_region(PanCJKVRegion::XK) // annotate with a presedo region called KangXi
        .collect::<RuneString>();
    assert_eq!(
        &result.chars().collect::<Vec<_>>()[..],
        &[
            '\u{6211}',
            '\u{E01EF}', // this variation selector is inserted
            '\u{030C}',
            '\u{4EEC}',
            '\u{E01EE}', // this is untouched
            '\u{0301}'
        ]
    );
    assert_eq!(2, result.runes().count()); // rune count does not change
}
```

<br>

#### License

<sup>
Licensed under either of <a href="LICENSE-APACHE">Apache License, Version
2.0</a> or <a href="LICENSE-MIT">MIT license</a> at your option.
</sup>

<br>

<sub>
Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in this crate by you, as defined in the Apache-2.0 license, shall
be dual licensed as above, without any additional terms or conditions.
</sub>
