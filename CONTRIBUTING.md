# Contributing

Thanks for your interest in improving PDF Optimizer! Here is how you can help.

## Reporting bugs

Open a [GitHub issue](https://github.com/JuanLara18/pdf-optimizer/issues) with:

- Steps to reproduce (input file characteristics, command used).
- Expected vs. actual behavior.
- Python version and OS.

## Suggesting features

Open an issue describing the use case and why existing options don't cover it.

## Submitting patches

1. Fork the repo and create a feature branch from `main`.
2. Install dev dependencies: `poetry install`.
3. Make your changes — keep diffs focused on a single concern.
4. Run linters and tests:
   ```bash
   poetry run black --check .
   poetry run flake8
   poetry run pytest
   ```
5. Open a pull request. Describe *what* changed and *why*.

## Style

- Code is formatted with [Black](https://black.readthedocs.io/) (line length 100).
- Linting via [Flake8](https://flake8.pycqa.org/) with the same line length.
- Follow the conventions already present in the codebase.

## License

By contributing you agree that your contributions will be licensed under the [MIT License](LICENSE).
