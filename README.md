# Vadalog-DLV^E Benchmarking

## Foreword

* The Vadalog system is not included in this repository, and 
  it will be made available upon request.
* The folder `final_results` contains the experimental results for the _PSC_
    benchmark and for each query over the _Doctors_ dataset.

## Preliminaries

- Clone the repository:
```
git clone https://github.com/TeodoroBaldazzi/Shy-Warded-Datalog-KR2022.git --recursive
```

- Make sure you have Python 3.8 or later versions.

- Install [Pipenv](https://pipenv.pypa.io/en/latest/)
```
pip install pipenv
```

- Create a virtual environment and install the dependencies
```
pipenv shell --python=python3.8
pipenv install
```

- Add the current directory to PYTHONPATH (this has to be done whenever a new terminal is spawned):
```
export PYTHONPATH=${PYTHONPATH:+$PYTHONPATH:}$(pwd)
```

The following is needed only if Vadalog is requested.

- Install JDK 15. Using [sdkman](https://sdkman.io/):
```
sdk install java 15.0.2-open
sdk use java 15.0.2-open
```

- Install Maven 3+
```
sdk install maven 3.8.4
sdk use maven 3.8.4
```

- Copy the Vadalog project in `third_party/vadalog-engine-bankitalia`:

- Build the Vadalog project:
```
cd third_party/vadalog-engine-bankitalia
mvn -f pom.xml package
```

## Optional: use Docker

Instead of running the following commands on the host machine,
you could use the Docker image. To build:
```
./scripts/build-docker.sh
```

To run a shell inside the container:
```
./scripts/run-docker.sh
```

## Wrappers usage

The generic entrypoint for the tools is `bin/run-engine`. Usage:
```
Usage: run-engine [OPTIONS]

  Run a Datalog engine with a program and a dataset.

Options:
  --name TEXT
  -p, --program FILE           [required]
  -d, --dataset FILE
  --timeout FLOAT RANGE        [x>=0.0]
  -t, --tool-id [vadalog|dlv]  [required]
  --tool-config TEXT           custom configuration for the tool
  --run-config TEXT            custom configuration for the run
  --working-dir TEXT           working directory where to save results. If the
                               directory already exists, a prompt will ask
                               confirmation for removal.
  --force                      Force removal of working directory if already
                               exists.
  --help                       Show this message and exit.
```

The `--tool-id` argument allows to switch Datalog backend.
Currently the only backend supported are `vadalog` and `dlv`.

E.g. to launch DLV^E for a reasoning task:
```
./bin/run-engine \
  --program third_party/TOCL_dlvEx/examples/father_person.rul \
  --dataset third_party/TOCL_dlvEx/examples/person.data \
  --tool-id dlv \
  --working-dir results \
  --force
```

To launch Vadalog for a reasoning task:
```
./bin/run-engine \
  --program programs/psc/vadalog.txt \
  --tool-id vadalog \
  --working-dir results \
  --force \
  --run-config '{"binds": ["keyPerson:csv:./datasets/psc/vadalog/0001000/keyPerson", "person:csv:./datasets/psc/vadalog/0001000/person", "control:csv:./datasets/psc/vadalog/0001000/control"]}'
```

## Run experiments

- Generate datasets
```
./scripts/generate-datasets
```
- Generate programs
```
./scripts/generate-programs
```

To run the following commands without Vadalog, remove the `--tool vadalog` parameter.

### PSC

Launch experiment on the `psc` dataset, comparing `vadalog` and `dlv`:

```
./benchmark/experiments/run-scalability-experiment --timeout 300.0 \
    --output-dir results \
    --tool dlv \
    --tool vadalog \
    --dataset-dir datasets/psc \
    --program-dir programs/psc
```

### Doctors dataset


Launch experiment on the `doctors` dataset 
with query `q01`, comparing `vadalog` and `dlv`:

```
./benchmark/experiments/run-scalability-experiment --timeout 300.0 \
    --output-dir results \
    --tool dlv \
    --tool vadalog \
    --dataset-dir datasets/doctors \
    --program-dir programs/doctors-q01
```

To run all queries:

```
./benchmark/experiments/run-all-doctors.sh
```

### Doctors dataset


Launch experiment on the `doctors` dataset 
with query `q01`, comparing `vadalog` and `dlv`:

```
./benchmark/experiments/run-scalability-experiment --timeout 300.0 \
    --output-dir results \
    --tool dlv \
    --tool vadalog \
    --dataset-dir datasets/doctors \
    --program-dir programs/doctors-q01
```

To run all queries:

```
./benchmark/experiments/run-all-doctors.sh
```

## Parse result

Join time results, e.g.:

```
python scripts/join --results-dir final_results/psc --column time_end2end
```

Average result across `doctors` queries, e.g.:
```
python scripts/average                     \
    --result-dir final_results/doctors-q01 \
    --result-dir final_results/doctors-q02 \
    --result-dir final_results/doctors-q03 \
    --result-dir final_results/doctors-q04 \
    --result-dir final_results/doctors-q05 \
    --result-dir final_results/doctors-q06 \
    --result-dir final_results/doctors-q07
```
