# SKYsense AI: Demonstration Cloud Specimens

This directory contains representative, unmanipulated cloud images selected from the verified dataset splits for demonstration purposes and live inference testing.

> **Notice:** These are authentic research specimens from the CCSN cloud database. No fake predictions or artificial outputs are stored. The web application dynamically runs deep learning inference when any sample is analyzed.

## Directory Structure

```text
demo_images/
├── labels.json           # Machine-readable ground truth labels and specimen metadata
├── low_medium/           # Stratus, Altostratus, Nimbostratus specimens (4 images)
├── medium_heavy/         # Cumulonimbus, Towering Cumulus specimens (4 images)
└── no_low/               # Cirrus, Altocumulus, Contrail specimens (4 images)
```

## Summary of Demonstration Specimens

| Category | Category Label | Cloud Genus | Filename | Resolution |
| :--- | :--- | :--- | :--- | :--- |
| `low_medium` | Low to Medium Rain | Altostratus (As) | `As_As-N007.jpg` | 400x400 |
| `low_medium` | Low to Medium Rain | Nimbostratus (Ns) | `Ns_Ns-N009.jpg` | 400x400 |
| `low_medium` | Low to Medium Rain | Stratus (St) | `St_St-N023.jpg` | 400x400 |
| `low_medium` | Low to Medium Rain | Stratocumulus (Sc) | `Sc_Sc-N003.jpg` | 400x400 |
| `medium_heavy` | Medium to Heavy Rain | Cumulonimbus (Cb) | `Cb_Cb-N002.jpg` | 400x400 |
| `medium_heavy` | Medium to Heavy Rain | Cumulus (Cu) | `Cu_Cu-N001.jpg` | 400x400 |
| `medium_heavy` | Medium to Heavy Rain | Cumulonimbus (Cb) | `Cb_Cb-N015.jpg` | 400x400 |
| `medium_heavy` | Medium to Heavy Rain | Cumulonimbus (Cb) | `Cb_Cb-N022.jpg` | 400x400 |
| `no_low` | No to Low Rain | Cirrus (Ci) | `Ci_Ci-N010.jpg` | 400x400 |
| `no_low` | No to Low Rain | Cirrocumulus (Cc) | `Cc_Cc-N005.jpg` | 400x400 |
| `no_low` | No to Low Rain | Cirrostratus (Cs) | `Cs_Cs-N005.jpg` | 400x400 |
| `no_low` | No to Low Rain | Altocumulus (Ac) | `Ac_Ac-N008.jpg` | 400x400 |

*Total specimens: 12*
