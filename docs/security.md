# Threat model

Written before the first output left the founders' laptop (issue #24), and
checked against the actual generated pages rather than assumed. Update it
when the answers change; decisions go in [decisions.md](decisions.md).

The asset being protected is **a household's photo archive**: 4,547 files,
five and a half years, three pets, two people, and the inside of their home.
This is among the most sensitive personal data most people hold, and unlike
a password it cannot be rotated after a leak.

---

## What is actually in the output today

Measured on `izzy.html` (1,353 moments) and `oakley.html`:

| | in the page? | note |
|---|---|---|
| Photo thumbnails | **yes**, 200px | the point of the page |
| Absolute source paths | no | 0 occurrences; `--originals` (#13) would add them |
| GPS coordinates | no | 0 occurrences, though 2,944 media rows carry them in `moments.json` |
| Device models | **yes** | "Pixel 5", "Pixel 3 XL" — in the expanded burst |
| Contributor names | **yes** | "Matt", "Renee" — first names only |
| Full-resolution originals | no | never; thumbnails are re-encoded crops |
| `moments.json` | no | the page is self-contained; the data file is not shipped |

`moments.json` and `pet.json` hold far more — absolute paths for all 4,547
files, GPS on 2,944 of them, every filename — and are gitignored and never
shared. **The page is the only artifact that leaves the laptop.**

---

## Threats, and what is done about each

### 1. A shared page reaches someone it was not meant for

**Most likely threat, by a distance.** Links leak through group chats,
browser sync, referrer headers and forwarded mail. An unguessable URL is not
access control.

*Today:* nothing is hosted. Output is a local file, hand-delivered. That is
the mitigation, and it is why #29 sends files rather than links.
*Deferred:* real auth before anything is hosted (#25, #27). A password on a
static host is the minimum; Cloudflare Access with an email allowlist is the
cheap correct answer.

### 2. Location disclosure

97% of media carries GPS, and the largest cluster is the house. A page that
included coordinates would publish a home address to anyone who received it.

*Today:* no coordinates reach the page — verified, 0 occurrences.
*Rule for #11 (places):* a place gets a **name**, never a coordinate, in the
page. Reverse geocoding must not call a network service with the user's
coordinates. `moments.json` may keep GPS; it never ships.

### 3. Originals leaving the device

The vision (§4) says originals stay on the phone. 19 GB of full-resolution
photos is the crown jewels, and the product has no need for them.

*Today:* held. Thumbnails are re-encoded 200px crops; EXIF does not survive
re-encoding, so the shipped images carry no embedded GPS or camera metadata.
*Rule for #13 (downloads):* `--originals` emits `file://` links and must stay
**off by default** and never be used for a page that will be shared. Verified
today that the flag off leaves 0 paths in the HTML.
*Rule for #26/#27:* a server stores moments and thumbnails only. If a server
ever needs an original, that is a design error.

### 4. Other people's pets, homes and children

The archive contains friends' dogs, the inside of friends' homes, and other
people's children. Those people did not consent to a product.

*Today:* no identity of any kind is extracted. The detector counts persons;
it never says who. Faces are never embedded, clustered or matched.
*Rule:* this stays true. Face recognition is a different product with a
different consent posture — see the data-model's *what it does not include*.
*Practical:* before sending a pet's timeline to its owner (#29), skim it. A
photo of someone else's kid is not a bug the code can catch.

### 5. A contributor leaves, or the relationship ends

Renee's 2,142 photos are in the merged timeline; 103 moments contain frames
from both people. Photos already sent cannot be recalled.

*Today:* undefined, and that is the problem. **Blocking issue #20.**
*Rule:* decide the ownership model before building any sharing (#25). The
dangerous outcome is not an error — it is a timeline that keeps rendering
with a hole nobody was told about.

### 6. A phone is lost or compromised

If the app has full library access, what does an attacker gain?

*Answer: nothing new.* The index is derived from photos already on that
device. An attacker with the phone already has the originals. This threat is
genuinely mild, and worth stating so it is not over-engineered against.
*Caveat:* if a phone ever holds **other** contributors' thumbnails, that
changes — a lost phone would then leak someone else's photos. Keep that in
mind for #26.

### 7. Third-party services

*Today:* none. Detection is a local model, there are no analytics, no
telemetry, no network calls at render time. The only remote resources in the
page are Google Fonts stylesheets.
*Note:* Google Fonts means every viewer's browser makes a request to Google
carrying their IP and referrer. Harmless for a family page, worth knowing.
Inlining the fonts would remove it.

### 8. The pipeline itself

*Today:* photos are read, never written. The cache and `moments.json` are
derived and reproducible. No destructive operation exists in either script.
Nothing from the archive can reach git — `.gitignore` covers `*.jpg`,
`*.json`, `*.html`, `*_assets/`, `.cache/`, `pics/`, and every commit is
checked with `git diff --cached --name-only`.

---

## Rules that follow from this

1. **The page is the only thing that leaves the laptop.** Never ship
   `moments.json`, `pet.json`, `digest.json` or the cache.
2. **No coordinates in a page, ever.** Names only.
3. **No originals in a shared page.** `--originals` is local-only, off by
   default.
4. **No identity extraction.** Persons are counted, never named or matched.
5. **Nothing is hosted without real auth.** Hand-delivered files until #25
   and #27 are answered.
6. **Ownership before sharing.** #20 blocks #25.
7. **Skim before sending.** The archive contains other people's lives.

## What changed because of this document

- `--originals` (#13) is specified off-by-default and local-only, with a
  verification step, rather than a plain flag.
- #11 (places) is constrained to names in the page and offline geocoding,
  before it is built.
- #20 (ownership) is promoted to a blocker for #25 rather than a parallel
  concern.
- #29 (sharing with friends) gains an explicit pre-send check: run the leak
  grep, and skim the page for other people's children.
