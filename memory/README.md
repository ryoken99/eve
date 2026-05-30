# Eve Local Memory

This directory is the local private memory home for Eve.

The repository may contain only:

- empty folder skeletons through `.gitkeep`;
- generic `README.md` files;
- safe `.example.json` and `.example.yaml` templates;
- generic policies that do not contain private memories.

Do not commit real local data:

- transcripts;
- vector databases;
- Chroma files;
- handoffs;
- rollups;
- dreams;
- candidates;
- private identity cards;
- personal memory;
- logs;
- runtime state;
- secrets or tokens.

PC2 (`E:\eve`) is Eve's primary runtime home. PC1 can pull the architecture and code, but private memory remains local to PC2.
