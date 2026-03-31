from huggingface_hub import snapshot_download
import os

#   RedHatAI/DeepSeek-R1-Distill-Qwen-7B-quantized.w8a8
#   jakiAJK/DeepSeek-R1-Distill-Qwen-7B_GPTQ-int4
#   jakiAJK/DeepSeek-R1-Distill-Qwen-7B_AWQ
#   deepseek-ai/DeepSeek-R1-Distill-Llama-8B
#   RedHatAI/DeepSeek-R1-Distill-Llama-8B-quantized.w8a8
#   jakiAJK/DeepSeek-R1-Distill-Llama-8B_GPTQ-int4
#   jakiAJK/DeepSeek-R1-Distill-Llama-8B_AWQ
snapshot_download(repo_id="Qwen/Qwen3-8B-AWQ",
                  cache_dir='/home/gluo/models',
                  ignore_patterns=["*.msgpack", "*.h5"])
