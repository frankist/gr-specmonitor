Hello there!

In this repository, you can find the code for my dataset collection framework. You can also find here some of the tools I wrote/used to train my deep learning object detection algorithms to identify RF signals.

# Installation

I wrote a small script that installs the main dependencies of this repository. You can find it in

    scripts/install.sh

# Usage

## Dataset Collection Framework

There are some examples in the directory ```examples``` for generating your own dataset. 

### Run a simple simulation example

If you are not within reach of any USRP pair (one Tx and one Rx) at the moment, you can run the simulation example in ```examples/sim_dataset_generation```.

Enter the directory ```examples/sim_dataset_generation``` and run

    python sim_awgn_luigi.py

In the directory ```tmp/```, a directory called ```sim_dataset``` will be created with several subdirectories. If you open the ```RFVOCFormat/Images```, you can see several spectrograms of WiFi, 4-channel PSK, and LTE transmissions.

### Basic Introduction

In the previous example, several directories have been created with many files inside. These files represent intermediate data that the specmonitor framework generates to arrive to the final dataset. Each file represents the output of a batch job that is specified by the experimenter.

Like GNU Make, the specmonitor framework allows you to build complex pipelines of batch jobs, handling dependencies between them. We use the [luigi](https://github.com/spotify/luigi) to handle this pipeline workflow.

To set your workflow, you need to create three basic files: (i) a python file where you specify the type, name, and dependencies of the tasks/jobs of your workflow, (ii) a python file where you specify the combinations of arguments your jobs can take, (iii) a .cfg file where you set what tasks to run of your workflow, and output directory. You can check in ```example/sim_dataset_generation``` the (i) sim_awgn_luigi.py, (ii) task_params.py, and (iii) luigi.cfg, examples of these files.


