
## Developing pdr-utils

This README provides instructions for setting up the development environment and testing the library.

### Installation from source

In a new terminal:

```console
# clone the repo and enter into it
git clone https://github.com/oceanprotocol/pdr-utils
cd pdr-utils

# Create & activate venv
python -m venv venv
source venv/bin/activate

# Install modules in the environment
pip3 install -r requirements.txt
```

### Testing

To run the tests, use the following command in the terminal:

```console
pytest
```

### Example Usage

You can interact with pdr-utils in Python. Launch a Python console from the same terminal:

Then, in the Python console, you can use the library like this:
```python
from pdr_utils.subgraph import query_subgraph
```