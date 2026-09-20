# Scientific release checklist — ANTMUX-X72

## A. Identity

- [ ] Create or confirm an ORCID iD.
- [ ] Verify the ORCID email.
- [ ] Add the ORCID iD to `CITATION.cff` and `.zenodo.json`.
- [ ] Add the final Zenodo record to the ORCID record after publication.

No institutional affiliation is required to obtain an ORCID iD.

## B. Freeze a citable software version

- [ ] Merge only the reviewed scientific-package changes intended for release.
- [ ] Rerun `research/REPRODUCIBILITY.md`.
- [ ] Record Python, Node and OS versions.
- [ ] Confirm `git status` is clean.
- [ ] Create a version tag, candidate: `x72-daat-paths-v0.2.0`.
- [ ] Create a GitHub Release from that exact tag.

Do not retag a different commit after a DOI has been created.

## C. DOI path

Two valid Zenodo workflows are possible.

### Option 1 — Manual Zenodo upload first

Use this when the DOI must appear inside the preprint before publication.

- [ ] Create a Zenodo draft.
- [ ] Choose the appropriate resource type.
- [ ] Reserve a DOI in the draft.
- [ ] Put the reserved DOI into the preprint and citation metadata.
- [ ] Upload the exact release artifact and preprint.
- [ ] Review metadata.
- [ ] Publish the Zenodo record.

The DOI becomes registered when the Zenodo record is published.

### Option 2 — GitHub release integration

Use this for automatic software archiving.

- [ ] Link GitHub to Zenodo.
- [ ] Enable the `Topbrutus/Antmux` repository in Zenodo.
- [ ] Verify `CITATION.cff` and `.zenodo.json`.
- [ ] Create the GitHub Release.
- [ ] Verify Zenodo archived the release and assigned the DOI.
- [ ] Add the DOI back to the repository documentation.

Important: Zenodo's GitHub integration does not currently support pre-reserving the DOI before the GitHub release. Manual upload does.

## D. Preprint quality gate

Before publishing the preprint:

- [ ] distinguish project-specific contributions from established mathematics;
- [ ] call theta a scalar phase angle / Givens parameter in the academic version;
- [ ] avoid calling the current implementation a quaternion neural network unless quaternion algebra is actually implemented;
- [ ] describe the visual-state union as noisy-OR-like, not probabilistic, unless a probability model is defined;
- [ ] retain the limitation that the current routing graph has two connected components;
- [ ] retain the limitation that binary64 reconstruction is approximate;
- [ ] retain the statement that no biological or physical law is claimed;
- [ ] add DOI and ORCID once available.

## E. Minimum artifact set

A citable release should contain at least:

- `research/PREPRINT_X72_DAAT_PATHS_v0.2.md`
- `research/REPRODUCIBILITY.md`
- `CITATION.cff`
- `.zenodo.json`
- source code for Z coupling and Stereo Source
- unit/adversarial tests
- a release tag and immutable commit SHA
- test log or machine-readable report

## F. After DOI

Once the DOI exists:

- [ ] cite it from the GitHub profile README;
- [ ] cite it from the Antmux README;
- [ ] add it to ORCID;
- [ ] use the DOI rather than screenshots as the primary scholarly reference;
- [ ] preserve social-media posts only as supplementary public timestamp evidence.

## G. Conference / journal targeting

Do not submit the same manuscript blindly to several communities. First decide the primary contribution:

- numerical / geometric method → numerical linear algebra or geometric information venue;
- artificial-life architecture → ALIFE / complex systems;
- cognitive architecture → BICA-like community;
- affective interface → affective-computing venue, only after empirical validation.

The first manuscript should stay narrow: **12-channel orthogonal coupling + stereo-Z source + reproducibility**.
