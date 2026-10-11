# Open-source references

Repository pages checked on 2026-10-11. The descriptions below summarize each
project's own README; they are not claims that we installed or independently
validated every workflow. The foundation used EdgarTools as an installed, tested
dependency. Later FinRobot source-port drafts are now preserved in the repository,
but are not integrated. See [expanded source audit](OPEN_SOURCE_AUDIT.md) and
[Claude Code handover](../HANDOVER_CLAUDE.md) for current scope and provenance.

| Project | Useful reference for this workbench | License / boundary |
|---|---|---|
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | Financial research workflows; deterministic computation alongside LLM narration; report generation. Its `finrobot_equity` directory includes an HTML/PDF report web app; `finrobot_desktop` provides a broader research workstation. | Apache-2.0. More infrastructure and provider configuration than this single Streamlit app. |
| [OpenBB](https://github.com/openbq-org/OpenBB) | Multi-provider data integration and APIs for research dashboards. | Apache-2.0 data platform. The former OpenBB-finance/OpenBB URL redirects here. |
| [OpenBB Workspace](https://github.com/OpenBB-finance/workspace) | React workspace and actual semantic design tokens, separately published from the data platform. | Public archived source checked at `be00e95019a55d57af146919ee46b7e1a4859226`; Apache-2.0 with NOTICE and component boundaries. Proprietary TradingView Advanced Charts is not distributed/licensed by the repository. Not yet ported or run here. |
| [EdgarTools](https://github.com/dgunning/edgartools) | SEC filing/XBRL parsing, dimensions, financial statement extraction, source inspection. This workbench already uses its filing parser. | MIT. Library, not a complete credit-research dashboard. |
| [FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) | Financial NLP, fine-tuning, sentiment and forecasting research examples. | MIT. Model/research focus; not a finished substitute for corporate credit analysis. |

## Reuse

[The MIT license](https://opensource.org/license/mit) allows copying, modification,
distribution and commercial reuse, provided its copyright and permission notices
are retained in copies or substantial portions. Check the actual license of the
specific files before reuse; an open GitHub repository is not automatically MIT.
Maintain attribution for copied code. Reusing a library does not remove the need
to verify accounting scope, source links and output accuracy.
