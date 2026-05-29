# Audit Summary — Lab 10: NER Pipeline + Hybrid Rules

**Date:** 2026-05-29


## 1. Pipeline
- **Model:** spaCy en_core_web_sm v3.8.0
- **Language:** English
- **Entity labels (baseline):** PERSON, ORG, GPE, DATE, NORP, MONEY, ELECTRONICS_COMPONENT

## 2. Important Entity Types for This Corpus
- PERSON -- religious figures and public intellectuals (14 in gold)
- ORG    -- tech companies and institutions (8 in gold)
- GPE    -- geo-political entities (4 in gold)
- DATE   -- calendar dates + Usenet RFC-2822 header dates (12 in gold)
- ELECTRONICS_COMPONENT -- domain-specific, not in spaCy (11 in gold)
- NORP   -- nationalities/religions (3 in gold)

## 3. What Baseline Found Well
- Standard ORG: Intel, MIT Media Lab, Hewlett-Packard
- GPE: Poland, Rome, Arabia, Skopje
- PERSON: Richard Dawkins, David Hume, Mother Teresa, Jesus Christ
- DATE fragments: November 1971, June 1979, 2006
- NORP: Christian

## 4. What Baseline Missed
- All electronics components (10/11 missed -- no training data in sm model)
- Full RFC-2822 Usenet dates (only year fragment tagged by baseline)
- Compound religious names: Holy Spirit, John the Baptist, Pope John Paul II
- Rare PERSON: God
- Religious DATE: Pentecost

## 5. Hybrid Rules Added
- **ELECTRONICS_COMPONENT**: PhraseMatcher on 26-term vocabulary; 0->10 correct
- **RELIGIOUS_FIGURE -> PERSON**: PhraseMatcher 22 names + longest-span dedup; 9->12 PERSON correct
- **USENET_DATE**: RFC-2822 regex + asymmetric overlap; 6->9 DATE correct

## 6. What Rules Improved
Rule 1: ELECTRONICS_COMPONENT 0->10 correct (+10).
Rule 2: PERSON 9->12 correct (+3), boundary 3->1 (-2).
Rule 3: DATE 6->9 correct (+3), boundary 5->2 (-3).
Dedup: FP 12->8 (-4).

## 7. Error Categories (Most Frequent)
- boundary_error (10): article prefix, partial multi-word spans -- most frequent
- false_positive (8): spaCy ORDINAL/CARDINAL/DATE noise on non-entity tokens
- missed (2): 'God' (PERSON) and 'Pentecost' (DATE)
- type_error (1): 'Islam' ORG->NORP

## 8. Evaluation Results
### Baseline
- Correct: 24
- Missed:  13
- FP:      12
- Rough P/R/F1: P=0.462  R=0.453  F1=0.457
### Hybrid
- Correct: 40
- Missed:  2
- FP:      8
- Rough P/R/F1: P=0.678  R=0.755  F1=0.714

## 9. What to Fix Next
- Strip leading article from ORG/DATE boundary errors ('The Council' -> 'Council')
- Add RELIGIOUS_DATE rule: Pentecost, Easter, Ramadan, Passover
- Add 'Islam' to NORP phrase list
- Whitelist filter for common spaCy FPs (ORDINAL 'first', DATE on measurements)
- Fine-tune en_core_web_sm NER on a small annotated 20-Newsgroups sample
