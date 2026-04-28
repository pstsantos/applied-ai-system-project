# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**Aura**

---

## 2. Intended Use  

Aura recommends songs from a small catalog based on a user's taste profile. You describe what you want — genre, mood, energy level, tempo — and it returns the five best matches with a short explanation for each.

It assumes the user can describe their preferences in advance. It does not learn from listening history or feedback. This is a classroom project, not a production system.

---

## 3. How the Model Works  

Every song in the catalog gets a score between 0 and about 0.95. The score is built from six parts.

The first two are binary — genre and mood either match or they don't. A genre match adds 0.13 points. A mood match adds 0.17 points.

The next four are based on distance. Energy, valence (how positive a song feels), danceability, and tempo are all compared to what the user asked for. The closer a song is to the target, the more points it earns. A perfect energy match adds 0.175 points; a song at the opposite extreme adds almost nothing.

If the user dislikes acoustic music, songs with high acousticness get a small penalty deducted from their score.

The five highest-scoring songs are returned as recommendations. No more than two songs from the same artist are included, to keep the list varied.

---

## 4. Data  

The catalog has 20 songs. Each song has a title, artist, genre, mood, and five numeric attributes: energy, tempo, valence, danceability, and acousticness.

Genres represented: pop (6 songs), rap (3), rock (3), lofi (3), indie pop (1), synthwave (1), jazz (1), ambient (1).

Moods represented: happy, intense, chill, focused, nostalgic, moody, melancholic, relaxed, passionate, epic.

Songs were added beyond the starter set to improve coverage across genres and moods. Some well-known tracks were included to make the catalog feel familiar.

What's missing: country, classical, folk, and R&B are not represented at all. Moods like sad, romantic, and angry have no catalog entries. The catalog skews heavily toward upbeat, high-energy music — quieter and more niche tastes are underserved.

---

## 5. Strengths  

The system works best for mainstream tastes. Pop, rock, and rap fans get five relevant results with no obvious misfits because those genres have the most catalog coverage.

The energy and tempo scoring does a good job separating very different use cases. A workout profile and a study profile return almost completely different songs, which is the right behavior.

The artist diversity cap helps. Without it, a lofi fan would get three LoRoom songs in their top five. The cap keeps the list from feeling like a single-artist playlist.

Each recommendation comes with a plain-language explanation showing which features contributed to the score. This makes it easy to understand why a song was picked, even when the result is surprising.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly.

**Catalog majority bias.** Pop has 6 out of 20 songs in the catalog, while jazz has 1 and ambient has 1. Because the genre bonus is a flat +0.13 regardless of catalog size, pop fans receive richer and more varied recommendations by default. A jazz fan earns that same bonus from exactly one song, then the rest of their results are driven by unrelated features.

**Extreme energy users are structurally disadvantaged.** The energy score is based on the distance between what the user wants and what a song offers. But the catalog's energy values cluster between roughly 0.28 and 0.93, so a user who wants very calm music (energy near 0.1) can never achieve a high energy score — the closest song is still far away. The formula treats all users as equally served, but quieter preferences are quietly penalized by what the catalog simply does not contain.

**Chill and lofi listeners get double jeopardy.** Every lofi and ambient song in the catalog has high acousticness (between 0.71 and 0.92). If a user says they dislike acoustic music, the system applies a penalty to all of these songs — the exact genre cluster that should be their best matches. No other genre has this problem: rock and rap songs have near-zero acousticness. The system inadvertently punishes users for choosing genres that happen to be acoustic by nature.

**The system has a hidden positivity bias.** When two songs score equally, the tiebreaker always favors the song with higher valence — meaning happier, more upbeat content wins by default. A user who explicitly wants dark or melancholic music will have every tie resolved in the opposite direction of what they asked for, with no indication in the explanation.

**Mood matching has no sense of adjacency.** A mood like "nostalgic" and a mood like "melancholic" describe similar emotional states, but the system treats them as entirely unrelated. If a user lists "nostalgic" and a song is tagged "melancholic," it receives zero credit for the match. At the same time, the continuous valence scoring quietly pushes results toward happier songs, so emotionally nuanced users may find their recommendations drift away from what they described.

**Acoustic preference is one-directional.** The `likes_acoustic` flag only removes a penalty — it never adds a reward. A user who loves acoustic music receives identical scores to a user who has no opinion about it. There is no way to express "give me more acoustic content"; the flag only works as a veto.

---

## 7. Evaluation  

Six user profiles were tested by running the recommender against the full catalog and inspecting the top 5 results for each.

**Profiles tested:**

- **Happy Pop Dancer** — high energy (0.82), happy mood, pop/indie pop, anti-acoustic. Represented the "mainstream" user the catalog is implicitly designed around.
- **Late-Night Study** — low energy (0.38), chill/focused mood, lofi/ambient, anti-acoustic. Tested how well the system handles a quiet-music user who dislikes acoustic despite needing it.
- **Workout Beast** — very high energy (0.92), intense mood, rap/rock, fast tempo (160 BPM). Tested the upper end of the energy spectrum.
- **Jazz Café** — low energy (0.37), relaxed mood, jazz, acoustic-positive. Tested a niche genre with minimal catalog coverage.
- **Melancholic Indie** — medium energy (0.70), nostalgic/moody, rock/indie pop, low target valence (0.30). Tested a user whose mood and valence preferences point in different directions from the catalog's dominant tone.
- **Synthwave Night Drive** — medium-high energy (0.75), moody, synthwave/pop, mid valence (0.50). Tested a niche genre with only one catalog entry.

**What the results showed:**

The Happy Pop Dancer and Workout Beast profiles returned the most coherent and consistent top 5s — all results felt relevant, scores stayed above 0.70, and there were no surprising entries. These profiles happen to align with the genres most represented in the catalog (pop, rock, rap).

The most surprising result was the Late-Night Study profile recommending **Bohemian Rhapsody** as its fifth pick. Bohemian Rhapsody is a rock epic — nothing close to lofi study music — yet it scored 0.56 because its slow tempo (72 BPM), low energy (0.40), and low danceability (0.40) numerically matched the study profile's continuous targets after the four actual lofi/ambient songs were exhausted. The system had no way to know it was the wrong genre once the mood and genre bonuses failed to apply.

The Jazz Café profile revealed the starkest quality cliff: the single jazz song scored 0.9467, then the next result dropped to 0.60 — a gap of 0.35 points. Recommendations 2–5 were all lofi songs, which share the right energy and tempo range but are clearly not jazz. This directly reflects the catalog having only one jazz song.

The Melancholic Indie profile showed how low target valence (0.30) competes against the rest of the scoring. Songs 3–5 bled into pop (Blinding Lights, Bad Guy) because rock/nostalgic is a thin cluster and pop songs with mid-valence happened to score similarly on the continuous features.

---

## 8. Future Work  

Expand the catalog. Twenty songs is too small. Niche genres like jazz and ambient need more entries before they can serve users well.

Add mood adjacency. "Nostalgic" and "melancholic" should get partial credit for each other. Right now the system treats every mood as completely unrelated to every other.

Fix the acoustic flag. Make it a two-sided preference instead of a one-sided penalty. A user who loves acoustic music should actually get boosted scores for acoustic songs, not just zero penalty.

Clamp the tempo input. If a user enters a tempo above 200 BPM, the normalization formula breaks and produces negative scores. A simple input check would fix this.

Add a discovery mode. Right now the system always ranks the closest match first. It would be interesting to have a mode that occasionally surfaces a surprising or unexpected song.

---

## 9. Personal Reflection  

**Biggest learning moment**

The biggest thing I learned is that catalog coverage matters more than scoring quality. I spent a lot of time tuning the weights and thinking about edge cases in the formula, but the Jazz Café profile showed the real problem in one result: one perfect match, then a 0.35-point drop to songs that had nothing to do with jazz. No amount of weight-tuning fixes a catalog with one jazz song. The data is the product.

**How AI tools helped — and when I had to double-check**

AI was genuinely useful for generating adversarial profiles I wouldn't have thought to test myself. The out-of-range tempo bug (target BPM of 250 producing negative scores) came from a suggestion to stress-test the boundaries of the normalization formula. I wouldn't have looked there on my own. But I had to run the tests myself to trust it. The AI described the bug correctly, but I didn't fully believe the `tempo fit (+-0.05)` explanation string was real until I saw it printed in the terminal. That's the pattern I'd follow again: use AI to point at the interesting places, then verify by running it yourself.

**What surprised me about how a simple algorithm "feels" like a recommendation**

The explanation strings. When the output says "mood match — happy (+0.17) · energy fit (+0.17) · genre match — pop (+0.13)" it genuinely feels like the system understands you. But it's just addition. The feeling of being understood comes entirely from the labels, not the logic. Renaming the fields to numbers would make it obvious that nothing smart is happening. That gap between what an algorithm does and what it feels like is something I want to keep thinking about.

**What I'd try next**

I'd add mood adjacency first — a small lookup table so that "nostalgic" gives partial credit to "melancholic" and "moody." That single change would fix the most common failure case I saw, where emotionally close songs got zero credit for mood. After that, I'd make the acoustic flag two-sided so `likes_acoustic: True` actually boosts acoustic scores instead of doing nothing. Both of these are small changes with a large impact on the users the current system underserves.
