# Network Visualization Stopwords

`stopwords_id.txt` is used only for Step 07 network visualization term filtering.
It is not a domain-specific dictionary and does not affect the scientific
pipeline steps 01-06.

Source:

- Repository: https://github.com/stopwords-iso/stopwords-id
- File: `stopwords-id.txt`
- License: MIT, copied in `stopwords_id_LICENSE.txt`

The application may add a small set of extra generic visualization stopwords in
`pipeline/aspect_network.py` for comparison modifiers or verbs that tend to
dominate graph nodes.
