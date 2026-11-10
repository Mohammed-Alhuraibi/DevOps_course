# Kubernetes slide sources

The twelve slides of the Kubernetes introduction are generated, not drawn by hand. They share the
design system of the containers lesson: the same palette, type, logos and slide frame. The only
differences are the footer ("Kubernetes", "N / 12") and the Kubernetes logo.

| File | What it is |
|------|------------|
| `build_k8s_slides.py` | the generator: Python 3 standard library only, writes `../slides/k8s-NN-<slug>.svg` |
| `../slides/k8s-00-what-we-build.svg` ... `k8s-11-compose-to-kubernetes.svg` | the slides, 1600x900, white background |

It reuses, without copying:

- [`docs/images/src/svgkit.py`](../../../docs/images/src/svgkit.py): design tokens, text measuring, SVG helpers, icons;
- [`docs/images/src/logos.json`](../../../docs/images/src/logos.json): the brand logos, including Kubernetes (`#326CE5`);
- [`docs/images/src/build_slides.py`](../../../docs/images/src/build_slides.py): slide helpers of the containers
  lesson (monospace text, badges, the laptop and server drawings).

Changing those files changes these slides too, so regenerate both lessons after editing them.

## Regenerate

From the repository root:

```console
laptop$ python3 kubernetes/images/src/build_k8s_slides.py
wrote kubernetes/images/slides/k8s-00-what-we-build.svg (37 KB)
...
```

The script estimates the width of every label and prints `warning: text may overflow` (exit code 1)
when one may not fit its box. Fix the layout until it is quiet, then check the SVGs in a browser at
about 880 px wide, the width GitHub shows them at.

## Where to change what

| You want to change | Edit in `build_k8s_slides.py` |
|--------------------|-------------------------------|
| one slide | its function `slide_00` ... `slide_11` |
| the order, file names or alt-text titles | the `SLIDES` list at the bottom |
| the footer and counter | `frame()` and `TOTAL` |
| how a pod, node, object, control plane or disk looks | the helpers at the top (`pod`, `node_card`, `obj`, `control_plane`, `disk`) |

The slides use only real names from [`kubernetes/manifests/`](../../manifests/): the `bugsquash`
objects, the `sha-0902b98` image tags, ports 8080 and 3000, `postgres-data` (5Gi), `bugsquash-ip`,
the ConfigMap keys and the 30 s tolerations. Update the slides when the manifests change.

## Logos and trademarks

The Kubernetes logo comes from Simple Icons, the same way as the other logos (see
[`docs/images/src/README.md`](../../../docs/images/src/README.md)). Simple Icons lists no licence for
it. Kubernetes is a registered trademark of the Linux Foundation, used here only to identify the
technology. Each SVG carries the shared credits comment at its top.
