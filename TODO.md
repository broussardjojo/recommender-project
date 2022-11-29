# To Do
- Ability to featurize a set of music
- Build out models to, given a featurized set of music, give recommendations
  - Multiple implementations incl.
    - KNN
    - cosine similarity
    - Matrix completion? (might be weird with our current featurization)

# Would be nice
- Add more data to the datasets
  - Or create a scraper to make own dataset - would NEED aio-http and batching for it to be any good
    - aiohttp for 'concurrent' queries
    - batching to reduce api limit penalty
- Interaction with spotify API to make the playlists

# Done
- Build out original dataset
- Featurize self data