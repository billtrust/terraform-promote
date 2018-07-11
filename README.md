# TFPromote

A CLI for promoting Terraform code through environments (dev, stage, prod, etc.)

## Required Directory Structure

This tool is useful only for a very prescriptive Terraform project structure.  It assumes the following:

* You store Terraform in a directory for each environment
* Within each directory files prefixed with that environment name (e.g. dev-) have variables specific to that environment and are expected to be different from other environments
* Files not prefixed with the environment name are expected to be able to be promoted (copied) from the source to the target environment exactly as is.

This is an example of the required directory structure:

```
app
    terraform
        dev
            dev-variables.tf
            dev-provider.tf
            iam.tf
            ecs.tf
        stage
            stage-variables.tf
            stage-provider.tf
            iam.tf
            ecs.tf
        prod
            prod-variables.tf
            prod-provider.tf
            iam.tf
            ecs.tf
```

## Installation

```shell
$ pip install tfpromote
```

## Usage

TFPromote will analyze the soure and target environment, show you the differences, prompt if you want to copy .tf files from the source to the target environment.

```shell
$ pwd
/devel/myapp/terraform/
$ tfpromote --to ./dev --from ./stage
```

If you have a compare tool installed (e.g. p4merge, kdiff, beyondcompare), you can specify that with the `--difftool` argument.

```
$ tfpromote --to dev --from stage --difftool p4merge
```

Or set your difftool with an environment variable so you don't have to type the argument each time.

```shell
$ export TFPROMOTE_DIFFTOOL=p4merge
$ tfpromote --to dev --from stage
```

To see a detailed diff printed to the screen if you don't have a difftool, use the `--printdiff` argument.

## Publishing Updates to PyPi

For the maintainer - to publish an updated version of TFPromote, increment the version number in version.py and run the following:

```shell
docker build -f ./Dockerfile.buildenv -t billtrust/tfpromote:build .
docker run --rm -it --entrypoint make billtrust/tfpromote:build publish
```

At the prompts, enter the username and password to the Billtrust pypi.org repo.

## License

MIT License

Copyright (c) 2018 Factor Systems Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
