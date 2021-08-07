#![deny(warnings, missing_docs, missing_debug_implementations)]
//! `rune`-based PanCJKV IVD Collection support
//! PanCJKV IVD Collection is an unregistered IVD collection,
//! that makes use of Unicode Variation Selectors to distinguish CJK ideograph glyphs on a per-region basis.
//!
//! This crate add support for PanCJKV IVD Collection support to `rune`-based iterators,
//! by allowing unannotated CJK ideograph abstract characters be transformed into annotated form explicitly.

use runestr::rune;

#[allow(dead_code)]
mod tables;

/// PanCJKV Regions
#[derive(Clone, Copy, Debug)]
pub enum PanCJKVRegion {
    /// Kāngxī
    XK,
    /// PRC
    CN,
    /// Republic of Singapore
    SG,
    /// ROC
    TW,
    /// Hong Kong SAR
    HK,
    /// Macao SAR
    MO,
    /// Malaysia
    MY,
    /// Japan
    JP,
    /// ROK
    KR,
    /// DPRK
    KP,
    /// Vietnam
    VN,
}

const PAN_CJKV_REGION_DATA: &[(PanCJKVRegion, char)] = &[
    (PanCJKVRegion::XK, '\u{E01EF}'),
    (PanCJKVRegion::CN, '\u{E01EE}'),
    (PanCJKVRegion::SG, '\u{E01ED}'),
    (PanCJKVRegion::TW, '\u{E01EC}'),
    (PanCJKVRegion::HK, '\u{E01EB}'),
    (PanCJKVRegion::MO, '\u{E01EA}'),
    (PanCJKVRegion::MY, '\u{E01E9}'),
    (PanCJKVRegion::JP, '\u{E01E8}'),
    (PanCJKVRegion::KR, '\u{E01E7}'),
    (PanCJKVRegion::KP, '\u{E01E6}'),
    (PanCJKVRegion::VN, '\u{E01E5}'),
];

#[allow(dead_code)]
const PAN_CJKV_REGION_COUNT: usize = PAN_CJKV_REGION_DATA.len();

/// Annotate rune iterator items with PanCJKV region
pub trait PanCJKVAnnotate: Sized {
    /// Retrieves an iterator that transforms all runes representing CJK ideographs to its PanCJKV IVS
    /// form within a specific region.
    fn annotate_with_pan_cjkv_region(self, region: PanCJKVRegion) -> PanCJKVAnnotateIter<Self>;
}

impl<I> PanCJKVAnnotate for I
where
    I: Iterator<Item = rune>,
{
    fn annotate_with_pan_cjkv_region(self, region: PanCJKVRegion) -> PanCJKVAnnotateIter<Self> {
        PanCJKVAnnotateIter {
            runes: self,
            region_vs: PAN_CJKV_REGION_DATA[region as usize].1,
        }
    }
}

/// The iterator that annotates rune items with PanCJKV region
#[derive(Debug)]
pub struct PanCJKVAnnotateIter<I> {
    runes: I,
    region_vs: char,
}

impl<I> Iterator for PanCJKVAnnotateIter<I>
where
    I: Iterator<Item = rune>,
{
    type Item = rune;

    fn next(&mut self) -> Option<Self::Item> {
        use crate::tables::is_han_script_lo_character;
        let rune = self.runes.next()?;
        if let Some(ch) = rune.into_char() {
            if is_han_script_lo_character(ch) {
                let mut s = String::new();
                s.push(ch);
                s.push(self.region_vs);
                return Some(rune::from_grapheme_cluster(&s).unwrap());
            } else {
                return Some(rune);
            }
        } else {
            let chars = rune.into_chars();
            #[derive(Clone, Copy)]
            enum State {
                None,
                HanScriptLoCore(usize),
                HanScriptLoCoreAndVS(usize, usize),
            }

            let mut state = State::None;
            for (idx, ch) in chars.clone().enumerate() {
                match state {
                    State::None => {
                        if is_han_script_lo_character(ch) {
                            state = State::HanScriptLoCore(idx);
                        }
                    }
                    State::HanScriptLoCore(core_idx) => {
                        if idx == core_idx + 1 && is_vs(ch) {
                            state = State::HanScriptLoCoreAndVS(core_idx, idx);
                        }
                        break;
                    }
                    _ => unreachable!(),
                }
            }
            if let State::HanScriptLoCore(idx) = state {
                let mut str = String::new();
                str.extend(chars.clone().take(idx + 1));
                str.push(self.region_vs);
                str.extend(chars.skip(idx + 1));
                Some(rune::from_grapheme_cluster(&str).unwrap())
            } else {
                Some(rune)
            }
        }
    }
}

fn is_vs(ch: char) -> bool {
    let ch = ch as u32;
    if ch >= 0xFE00 && ch <= 0xFE0F {
        true
    } else if ch >= 0xE0100 && ch <= 0xE01EF {
        true
    } else {
        false
    }
}

#[cfg(test)]
mod tests {
    use runestr::RuneString;

    use crate::{PanCJKVAnnotate, PanCJKVRegion};

    #[test]
    fn test_han_with_ascent() {
        let test = RuneString::from_str_lossy("\u{6211}\u{030C}\u{4EEC}\u{E01EE}\u{0301}");
        assert_eq!(2, test.runes().count());
        let result = test
            .runes()
            .annotate_with_pan_cjkv_region(PanCJKVRegion::XK)
            .collect::<RuneString>();
        assert_eq!(
            &result.chars().collect::<Vec<_>>()[..],
            &[
                '\u{6211}',
                '\u{E01EF}',
                '\u{030C}',
                '\u{4EEC}',
                '\u{E01EE}',
                '\u{0301}'
            ]
        );
        assert_eq!(2, result.runes().count());
    }
}
