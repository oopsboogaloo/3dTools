# How to prompt FLUX.2 Klein

Hard-won rules for this pipeline. Every one of these cost a failed batch to learn,
and most of them are invisible until you look closely at the output — the model
never reports that it misunderstood you, it just confidently renders the wrong
thing.

**If you are an AI agent picking up this project: read this before writing any
prompt.** The failure modes below are not intuitive and you will hit them.

---

## The one-paragraph version

Klein renders what your words *most commonly mean*, not what you meant by them.
It has no way to signal a misunderstanding. So: never name a character (it writes
the name on the plate), never compare a creature to an animal you don't want
drawn, never assume a stated age or era will be honoured, and always count the
limbs. Ask for adults younger and children older than you actually want, keep
people seated, and add grain afterwards rather than asking for it.

---

## 1. Comparisons become the subject

**The single most expensive mistake in this project.** A size comparison is not
read as scale — it is read as *what to draw*.

| Prompt said | Klein drew |
|---|---|
| a dinosaur "about the size of a large deer" | a deer, wearing a saddle |
| a "sheep-sized" frilled dinosaur | a hairless sheep |
| a "crow-sized" feathered raptor | a crow |
| a dromaeosaur "the size of a large wolf" | a wolf |

Four prompts, four mammals, zero dinosaurs. The comparison was *always* the thing
that survived.

**Rule:** never use `size of a <animal>`, `<animal>-sized`, or `like a <animal>`
unless you would be happy receiving that animal. Give absolute measurements and
explicit anatomy instead:

```
BAD   a slender bipedal herbivore about the size of a large deer, with a saddle
GOOD  a slender bipedal dinosaur standing six feet tall at the hip, running on two
      powerful birdlike hind legs, a long stiff counterbalancing tail held straight
      out behind it, scaly hide, a small beaked head, no fur and no hooves
```

Naming what it is **not** ("no fur and no hooves") is worth the words. The same
trick fixes most of the failures below.

## 2. Words that mean something else to the model

- **"raptor"** means *bird of prey*. Asking for a "large feathered raptor riding
  mount" produced a saddled eagle. Say **dromaeosaur**, name the sickle claw on
  the second toe, and explicitly say "not a bird, no beak, a toothed jaw".
- **"piloting"** gets you an animal standing *on top of* a vehicle. Say "seated
  inside the cockpit".
- **"sculptor"** in a character's backstory put finished marble statues in a
  woodworker's shop. Describe the objects you want in frame, not the person's
  ambitions.

## 3. Naming a character makes Klein caption the image

A prompt beginning `portrait of Josiah Coyle, a heavily built blacksmith...`
rendered the words **JOSIAH COYLE** burned into the top-right of the plate, plus
smaller illegible text elsewhere in the same batch.

**Rule:** describe the person, never name them. Composite names afterwards with
`label.py` / `finish_set.py`, where you control the typeface.

This matters because the alternative fix — a negative prompt — costs you the
distilled model (negatives need `--model base`, which is glossier and less
filmic). Removing the name is free.

## 4. Klein gets ages wrong in both directions

Consistently, across every batch:

| Asked for | Got |
|---|---|
| a woman "in her mid thirties" | 45–50 |
| an outlaw "aged about forty" | 55–60, and heavyset rather than broad |
| a boy "of about seven" | about four |
| a girl "of about thirteen" | about seven |

**Children go the other way — they render YOUNGER.** Adults come back older than
asked; children come back younger, and childish descriptors ("scraped knees",
"grinning", "restless") drag the apparent age down further. Asking for thirteen
returned a seven-year-old; asking for eighteen returned a convincing sixteen.

**Rule:** for adults, ask for someone noticeably younger than you want. For
children and teenagers, ask for noticeably OLDER, and say "an adolescent, not a
small child" outright. This pipeline's `subjects.py` writes adult ages down by
10–15 years against the design document and still lands slightly old.

Also **describe build separately from age** — "broad-shouldered" on its own
drifts toward "stout".

## 5. Limb artefacts are a FRAMING problem, not a prompt problem

The most important rule here, and the one that cost the most to learn. Measured
across the Dino Weird West set:

| Subject type | Framing | Anatomical artefacts |
|---|---|---|
| 59 people | seated, waist-up, hands on knees | **0** |
| 21 creatures | full body | **10** (48%) |

Not one human in fifty-nine had an extra, fused or phantom limb. Nearly half the
creatures did: three forelimbs on a Baryonyx, a detached sickle claw floating
beside a Deinonychus, three hind feet on a Therizinosaurus, a Dryosaurus with
fused claw-mass feet and no arms at all.

The difference is **how many limbs the model has to keep count of**. A seated
waist-up human puts two hands in frame and no feet. A full-body quadruped
demands four legs, two arms, a tail and twenty claws simultaneously, and the
model loses count.

The proof is in the exception: the **Triceratops** is the cleanest creature in
the set, and it is the only one framed head-and-shoulders.

**Rules:**
- Frame creatures as close as the shot allows. Head-and-forequarters beats full
  body, and it is better for tokens anyway, since a token is a tight circular
  crop.
- Keep full body only where the silhouette *is* the subject. Sauropods survive
  it -- Diplodocus and Apatosaurus both came back clean, being four pillars and
  no claws.
- **Raise the batch size for creatures.** At a ~50% artefact rate a batch of 4
  often contains no clean candidate. This pipeline uses **12 for creatures, 4 for
  people** (`subjects.BATCH_BY_KIND`). Twelve costs about 25 seconds.
- Always check limb counts at 100%. At contact-sheet size a third arm reads as
  shadow.

Anatomical artefacts outrank every other defect, because they are the tell that
pulls players out of the fiction and starts the jokes about AI. A horse in the
background of a dinosaur setting is a smaller problem than a fused foot.

## 6. Hands deform in standing poses

Seated, waist-up, hands resting open on the knees is reliable across whole
batches. Standing three-quarter shots with hands near a belt or holster produced
merged or extra fingers in most of a batch of four.

**Rule:** default to seated framing for anything you need in volume. Accept that
standing shots need more culling.

## 7. The photographic era does not carry the costume

`1870s wet-plate collodion tintype` reliably produces a convincing 1870s
*photographic process* — and 1940s clothing inside it. The plate treatment
anchors the chemistry, not the wardrobe.

Older characters escaped this only by luck: "high-necked dark dress" and "heavy
knitted shawl" happen to be period-correct anyway, while "a bold patterned dress"
came back as a 1940s day dress.

**Rule:** specify the garment, not the decade. Name the actual construction —
bustle, basque bodice, leg-of-mutton sleeve, bib-front shirt, sack coat.

## 8. Grain cannot be prompted

"Heavy coarse film grain, dense silver halide texture" increases *process
artefacts* — scratches, tide marks, plate damage, chemical swirls, which are all
genuinely useful — but barely moves actual grain texture. Klein renders smooth at
4 steps and no amount of rephrasing changes it.

**Rule:** ask the prompt for plate damage; add grain in post with `filmgrain.py`,
where strength is a number you control and stays identical across a whole set.

## 9. Negative prompts are blunt instruments

Adding `bear, bear paws, claws` to fix Klein's habit of giving mammoths bear feet
*did* fix the feet — and also removed the shaggy coat, leaving a short-haired
elephant. Klein's "woolly" concept is entangled with "bear".

**Rule:** after a negative prompt, check what else disappeared. Don't just confirm
the artefact is gone.

## 10. Klein fills unspecified gaps with clichés

It follows explicit instructions well and invents badly. Anything you leave open
comes back as the most generic possible answer:

- Don't say "60s sci-fi vibe" — say "1960s atomic age polished chrome, fins,
  glowing dial readouts", or you get rusted dieselpunk.
- Don't leave the background unstated — say "orbiting a blue planet", or you get
  a generic starfield.
- Don't say "piloting" — say what the hands and trunk are doing.
- Don't leave ethnicity unstated across a family — Klein picks per seed, so
  siblings come out unrelated. Pin two or three shared traits per household.

## 11. Anatomy drifts toward the famous relative

Herbivores get carnivore heads. Both the Stegosaurus and the Kentrosaurus came
back with correct plated bodies wearing toothy theropod skulls. Sauropods come
back with necks far too short — the Diplodocus read as a hippo.

**Rule:** describe the head and neck separately and explicitly, in their own
clause: "a very small beaked head on a neck as long as its entire body, no teeth".

**Sauropod necks respond to this; herbivore heads do not.** Adding "a very small
narrow toothless beaked head, no teeth, not a predator" fixed the Diplodocus and
Apatosaurus necks completely, but the Stegosaurus and Kentrosaurus *still* came
back with toothy theropod skulls across a whole second batch. Some priors are
strong enough to survive explicit negation — when that happens, stop re-rolling
the prompt and either accept it or fix it in post.

---

## Checklist before submitting a batch

1. Any `size of a <animal>` phrasing? Remove it.
2. Any proper names? Remove them.
3. Age: adults 10–15 years YOUNGER than you want; children and teens OLDER.
4. Is the subject seated, if it's a person?
5. Is a creature framed as CLOSE as the shot allows, and batched at 12?
6. Are head, neck and limbs described explicitly, if it's a creature?
7. Is the garment named by construction rather than by decade?
8. Is the background stated, rather than left to the model?
9. Are you asking for grain? Stop — that's `filmgrain.py`'s job.

## After the batch comes back

Look at all four drafts at a reasonable size — `review_sheets.py` builds 2×2
contact sheets for this. Check specifically:

- **Limb counts, at 100%.** The worst defect and the least forgiving. Count arms,
  legs, feet and claws on every creature.
- **Hands.** The most common defect on people.
- **Text.** Klein writes captions and fake signatures into corners.
- **Anachronisms.** Modern kettles, cars in the background, wrong footwear.
- **Species drift.** Is it actually the animal you asked for, or its nearest
  mammal?

A successful exit code means nothing. At 4096² Klein returns blue fog and reports
success — see the resolution ceiling table in `README.md`.

---

*See `README.md` for the pipeline itself, the resolution ceilings, and the
model/licensing rationale. Failures logged during the Dino Weird West run are in
`redo.json`, each with its diagnosed cause.*
