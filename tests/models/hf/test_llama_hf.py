from _pytest.fixtures import FixtureRequest
from transformers import (
    PreTrainedModel,
    LlamaForCausalLM,
    LlamaConfig,
)
import torch

from fms.models.hf.llama.configuration_llama_hf import LLaMAHFConfig
from fms.models.hf.llama.modeling_llama_hf import LLaMAHFForCausalLM
from fms.models.llama import LLaMA, LLaMAConfig
from fms.testing._internal.hf.model_test_suite import (
    HFConfigTestSuite,
    HFModelEquivalenceTestSuite,
    HFModelGenerationTestSuite,
)
from fms.testing._internal.test_resource_utils import resource_path_fixture


class TestLlamaHF(
    HFConfigTestSuite, HFModelEquivalenceTestSuite, HFModelGenerationTestSuite
):
    """
    Model Test Suite for llamaHF
    """

    _model_class = LLaMA
    _config_class = LLaMAConfig
    _hf_model_class = LLaMAHFForCausalLM
    _hf_config_class = LLaMAHFConfig
    _hf_specific_params = ["eos_token_id", "bos_token_id"]
    _hf_forward_parameters = ["input_ids", "labels"]

    @resource_path_fixture(test_name="llama", prefix="model")
    def resource_path(self, request: FixtureRequest) -> str:
        return request.param

    def _oss_hf_model(self, hf_model: PreTrainedModel) -> PreTrainedModel:
        hf_config = hf_model.config
        oss_hf_model = LlamaForCausalLM(
            LlamaConfig(
                vocab_size=hf_config.vocab_size,
                hidden_size=hf_config.hidden_size,
                rms_norm_eps=hf_config.norm_eps,
                num_attention_heads=hf_config.nheads,
                num_hidden_layers=hf_config.nlayers,
                pad_token_id=hf_config.pad_token_id,
                intermediate_size=int(
                    hf_config.hidden_size * hf_config.hidden_grow_factor
                ),
                bos_token_id=hf_config.bos_token_id,
                eos_token_id=hf_config.eos_token_id,
                max_position_embeddings=hf_config.max_expected_seq_len,
            )
        )

        with torch.no_grad():

            oss_hf_model.model.embed_tokens.weight.copy_(hf_model.embedding.weight)
            i = 0
            for oss_hf_layer in oss_hf_model.model.layers:
                fms_hf_layer = hf_model.decoder.model.layers[i]

                # self attn
                oss_hf_layer.self_attn.q_proj.weight.copy_(
                    fms_hf_layer.attn.query.weight
                )
                oss_hf_layer.self_attn.k_proj.weight.copy_(fms_hf_layer.attn.key.weight)
                oss_hf_layer.self_attn.v_proj.weight.copy_(
                    fms_hf_layer.attn.value.weight
                )
                oss_hf_layer.self_attn.o_proj.weight.copy_(
                    fms_hf_layer.attn.dense.weight
                )
                oss_hf_layer.self_attn.rotary_emb.inv_freqs = (
                    hf_model.decoder.model.rot_emb.freqs
                )

                # mlp
                oss_hf_layer.mlp.gate_proj.weight.copy_(
                    fms_hf_layer.ff_sub_layer.wg.weight
                )
                oss_hf_layer.mlp.up_proj.weight.copy_(
                    fms_hf_layer.ff_sub_layer.w1.weight
                )
                oss_hf_layer.mlp.down_proj.weight.copy_(
                    fms_hf_layer.ff_sub_layer.w2.weight
                )

                # layer norm
                oss_hf_layer.input_layernorm.weight.copy_(fms_hf_layer.ln.weight)
                oss_hf_layer.post_attention_layernorm.weight.copy_(
                    fms_hf_layer.ff_ln.weight
                )

                # adjust q, k
                q = oss_hf_layer.self_attn.q_proj.weight.data
                q = (
                    q.view(hf_config.nheads, -1, 2, q.size(1))
                    .transpose(1, 2)
                    .reshape(*q.size())
                )
                oss_hf_layer.self_attn.q_proj.weight.copy_(q)

                k = oss_hf_layer.self_attn.k_proj.weight.data
                k = (
                    k.view(hf_config.nheads, -1, 2, k.size(1))
                    .transpose(1, 2)
                    .reshape(*k.size())
                )
                oss_hf_layer.self_attn.k_proj.weight.copy_(k)

                i = i + 1
            oss_hf_model.model.norm.weight = hf_model.decoder.model.dec_norm.weight
            oss_hf_model.lm_head.weight = hf_model.lm_head.weight

        return oss_hf_model
