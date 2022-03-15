from dataclasses import dataclass
import toml
import logging


@dataclass
class ModuleConfig:
    classname: str
    options: dict


@dataclass
class Config:
    title: str
    url_collector_config: ModuleConfig
    parser_config: ModuleConfig
    output_config: ModuleConfig
    log_level: int
    log_name: str
    limit: int
    delay: int

    @classmethod
    def from_toml(cls, path):
        parsed = toml.load(path)
        runner = parsed.get("runner", {})
        collector = parsed.get("url_collector", {})
        output = parsed.get("output", {})
        parser = parsed.get("parser", {})

        return cls(
            title=parsed.get("title"),
            log_level=getattr(logging, runner.get("log_level", "NOTSET")),
            log_name=runner.get("log_name"),
            limit=int(runner.get("limit", 0)),
            delay=int(runner.get("delay", 0)),
            url_collector_config=create_module_config(collector),
            parser_config=create_module_config(parser),
            output_config=create_module_config(output),
        )


def create_module_config(conf: dict) -> ModuleConfig:
    return ModuleConfig(
        classname=conf.get("classname"),
        options={k: v for k, v in conf.items() if k != "classname"},
    )
