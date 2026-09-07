# Third-party components

The MIT license in `LICENSE` covers the code and documentation written for this
project. The components below came from elsewhere and keep their own terms.

## LeRobot 0.5.1 (vendored)

- Location: `ai/lerobot_source/lerobot/`
- Upstream: https://github.com/huggingface/lerobot, tag `v0.5.1`
- License: Apache License 2.0 (`ai/lerobot_source/lerobot/LICENSE`)

A pinned copy is vendored rather than declared as a dependency so that the exact
training and inference code used for the published results stays reproducible
even if upstream changes. `ai/lerobot_source/UPSTREAM.md` records the tag, the
tag object hash and an aggregate SHA-256 over the tree, so the copy can be
verified against upstream. No patches were applied (`ai/patches/` is empty).

## Neuromeka indy7_ros2

- Location: `ros2_ws/src/indy7_ros2/`
- Upstream: https://github.com/neuromeka-robotics/indy-ros2
- License: not distributed with the sources we received

Contains the Indy7 driver, interface definitions and robot description
(URDF/xacro and meshes) for the arm used in the experiment. Meshes and URDFs for
the other Neuromeka arms have been removed from this copy, since the experiment
only uses the Indy7; see `ros2_ws/src/indy7_ros2/indy_description/urdf/generate_all_urdfs.sh`.

**Open item:** upstream ships no license file, so the redistribution terms are
unclear. If you plan to reuse this subtree, check with Neuromeka. Consider
replacing it with a direct dependency on the upstream repository.

## Mand.ro Mark7 hand description

- Location: `ros2_ws/src/mark7/pipet_hand_mark7_description/`
- License: see `ros2_ws/src/mark7/pipet_hand_mark7_description/LICENSE`

The URDF, meshes and original attribution for the Mark7 hand. The driver,
message and teleoperation packages next to it (`pipet_hand_mark7_driver`,
`pipet_hand_mark7_msgs`, `pipet_hand_mark7_teleop`) were written for this
project and are MIT-licensed like the rest of the repository.

## Mark7 serial protocol document

- Location: `docs/mark7/Interface_with_Mark7 Hand_Simpler Protocol_20260305.pdf`

A manufacturer document, included because the driver implements the protocol it
describes.

**Open item:** redistribution rights have not been confirmed with Mand.ro. Drop
this file if the manufacturer objects.

## Recorded provenance paths

The JSON manifests under `experiment/manifests/` record absolute paths on the
machine where the data was acquired. They are left exactly as written, on
purpose: each condition manifest stores a `source_manifest_sha256` over the
manifest it was derived from, so editing those files would break the chain that
proves which raw episodes went into which training condition. The paths contain
no personal information.
