from typing import Optional

from transformers import PretrainedConfig

from fms.models.llama import LLaMAConfig

class LLaMAHFConfig(PretrainedConfig):
    model_type = "llama_hf"

    def __init__(
        self,
        src_vocab_size: Optional[int] = 32000,
        emb_dim: Optional[int] = 4096,
        norm_eps: float = 1e-6,
        nheads: int = 32,
        kvheads: int = 0,
        nlayers: int = 32,
        pad_token_id: int = -1,
        hidden_grow_factor: float = 8 / 3,
        multiple_of: float = 256.0,
        activation_fn: str = "swish",
        p_dropout: float = 0.0,
        max_expected_seq_len: int = 2048,
        use_cache: bool = True,
        eos_token_id: int = 2,
        bos_token_id: int = 1,
        is_decoder: bool = True,
        **kwargs,
    ):
        self.src_vocab_size = src_vocab_size
        self.emb_dim = emb_dim
        self.norm_eps = norm_eps
        self.nheads = nheads
        self.kvheads = kvheads
        self.nlayers = nlayers
        self.hidden_grow_factor = hidden_grow_factor
        self.multiple_of = multiple_of
        self.activation_fn = activation_fn
        self.p_dropout = p_dropout
        self.max_expected_seq_len = max_expected_seq_len
        self.use_cache = use_cache
        super().__init__(
            pad_token_id=pad_token_id,
            eos_token_id=eos_token_id,
            bos_token_id=bos_token_id,
            is_decoder=is_decoder,
            tie_word_embeddings=False, # this is handled by the underlying model
        )

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path, **kwargs) -> "PretrainedConfig":
        config_dict, kwargs = cls.get_config_dict(pretrained_model_name_or_path, **kwargs)

        return cls.from_dict(config_dict, **kwargs)

    @classmethod
    def from_fms_config(cls, config: LLaMAConfig, **hf_kwargs):
        config_dict = config.as_dict()
        config_dict["pad_token_id"] = config_dict.pop("pad_id")
        return cls.from_dict(config_dict, **hf_kwargs)