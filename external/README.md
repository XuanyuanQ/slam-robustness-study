# External Dependencies

Use this folder for third-party source code that you do not want to mix with your own project code.

For this project, the official ORB-SLAM3 repository should be cloned into:

```text
external/ORB_SLAM3/
```

Suggested command:

```bash
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git external/ORB_SLAM3
```

Notes:

- Keep your own implementation in `src/`.
- Treat everything in `external/` as third-party code.
- Do not edit the upstream source unless you explicitly want a local modification.

