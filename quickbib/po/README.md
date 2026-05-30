# QuickBib Translations

Translations are stored as gettext-style PO files in this directory.

- `en/LC_MESSAGES/quickbib.po` is the source of truth.
- Each translation must live under a language-code directory, for example:
  - `fr/LC_MESSAGES/quickbib.po`
  - `pt_br/LC_MESSAGES/quickbib.po`
  - `zh_cn/LC_MESSAGES/quickbib.po`
- Each message uses `msgid` for the English source text and `msgstr` for the
  translated text.

QuickBib picks translations in this order:

1. `LC_ALL` (if set)
2. `LC_MESSAGES` (if set)
3. `LANG` (if set)
4. System locale from Qt (for example `fr_FR`)
5. Locale language fallback (for example `fr`)
6. `en`

## Add a new language

1. Copy `en/LC_MESSAGES/quickbib.po` to a new language directory (for example
   `de/LC_MESSAGES/quickbib.po`).
2. Translate `msgstr` values, but keep `msgid` unchanged.
3. Run:

```bash
python validate_po.py --validate
```

4. Open a pull request.

## Update source keys

When adding or removing calls like `tr("Text to translate")` in the source code,
refresh the PO files and then validate them:

```bash
python validate_po.py --extract
python validate_po.py --validate
```
