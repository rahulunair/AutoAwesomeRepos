## Awesome List generator

This repo has code that will fetch repos based on the topics of interest in `config.py` 
Genertes descriptions for each projects
Does a zero shot topic generation for the repos

## How to run

```bash
python ghub_fetch.py
```

Tweak the config.py to set the keywords you are interested in and run ghub_fetch.py. This will query github and download
all repos of interest, generates a relevancy score, brief description of the project etc. 

**TODO**: add repo quality score as well


After this is run, the data is saved in `./repo_lists/` directory. To autogenerate an `AwesomeList.md` markdown from this, use:


```bash
python csv_utils.py ./repo_lists/<csv_file_name.csv>  # this csv is the file that we got from the previous step
```

We are using a few language models here, `paraphrase-MiniLM-L6-v2` with sentence transformers for zero-shot topic generation, distbart for description generation etc.

## This code runs on Intel discrete GPUs(XPU)

For those folks who have Intel discerte GPUs, if you have pytorch and ipex for xpu devices installed, the NLP models would be much faster.


## Contributing

I have just started with the repo, need a lot of cleanup, will add details here later


