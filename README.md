# pure-pyawabi

`pure-pyawabi` is a pure python implementation of awabi(https://github.com/nakagami/awabi).

If you have Rust development environment, see also https://github.com/nakagami/pyawabi .

## Requirements

MeCab dictionary

ex) Ubuntu

```
$ sudo apt install mecab mecab-ipadic-utf8
```

## Install python package

```
$ pip install pure-pyawabi
```

## Example

```
>>> import pyawabi
>>> import pprint
>>> pp = pprint.PrettyPrinter()
>>> pp.pprint(pyawabi.awabi.tokenize("すもももももももものうち"))
[('すもも', '名詞,一般,*,*,*,*,すもも,スモモ,スモモ'),
 ('も', '助詞,係助詞,*,*,*,*,も,モ,モ'),
 ('もも', '名詞,一般,*,*,*,*,もも,モモ,モモ'),
 ('も', '助詞,係助詞,*,*,*,*,も,モ,モ'),
 ('もも', '名詞,一般,*,*,*,*,もも,モモ,モモ'),
 ('の', '助詞,連体化,*,*,*,*,の,ノ,ノ'),
 ('うち', '名詞,非自立,副詞可能,*,*,*,うち,ウチ,ウチ')]
>>> pp.pprint(pyawabi.tokenize_n_best("すもももももももものうち", 2))
[[('すもも', '名詞,一般,*,*,*,*,すもも,スモモ,スモモ'),
  ('も', '助詞,係助詞,*,*,*,*,も,モ,モ'),
  ('もも', '名詞,一般,*,*,*,*,もも,モモ,モモ'),
  ('も', '助詞,係助詞,*,*,*,*,も,モ,モ'),
  ('もも', '名詞,一般,*,*,*,*,もも,モモ,モモ'),
  ('の', '助詞,連体化,*,*,*,*,の,ノ,ノ'),
  ('うち', '名詞,非自立,副詞可能,*,*,*,うち,ウチ,ウチ')],
 [('すもも', '名詞,一般,*,*,*,*,すもも,スモモ,スモモ'),
  ('も', '助詞,係助詞,*,*,*,*,も,モ,モ'),
  ('もも', '名詞,一般,*,*,*,*,もも,モモ,モモ'),
  ('もも', '名詞,一般,*,*,*,*,もも,モモ,モモ'),
  ('も', '助詞,係助詞,*,*,*,*,も,モ,モ'),
  ('の', '助詞,連体化,*,*,*,*,の,ノ,ノ'),
  ('うち', '名詞,非自立,副詞可能,*,*,*,うち,ウチ,ウチ')]]
>>>
```
