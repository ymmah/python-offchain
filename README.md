# tb-wasm-machine-poc
PoC for process virtual machine to interpret WASM binaries within the context of the TB verification game and it's particular constraints

### Content Description
`argparser.py` is the interpreter. I'll change the name later.<br/>
`getobj.sh` dumps a hex file that's easy to read. you need [binaryen](https://github.com/WebAssembly/binaryen) for this to work.<br/>
`injected.wast` is the test file generated by [wasmfiddle](https://wasdk.github.io/WasmFiddle/).<br/>
The `c-samples` directory contains simple C files and their WAST translation for anyone who wants to get a feel for it.<br/>

### Running the Sample
To be able to run the code as it is right now, you need to get the binary. I'm using [binaryen](https://github.com/WebAssembly/binaryen).<br/>
Our implementation will not run on python2.x.<br/>

To run the interpreter you should call:<br/>
```bash

python3 argparser.py --wasm ./injected.wasm

```
