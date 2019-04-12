import gzip
import json
import tarfile
import shutil

import yaml
import pie

__all__ = ["fasten_model"]


def _removeFile(src, tgt, remove):
    """Remove nameToDelete from tarfile filename."""
    original = tarfile.open(src)
    modified = tarfile.open(tgt, 'w')
    for info in original.getmembers():
        if info.name == remove:
            continue
        extracted = original.extractfile(info)
        if not extracted:
            continue
        modified.addfile(info, extracted)
    original.close()
    modified.close()


def fasten_model(input_file: str, target_file=None):
    """ Convert a model label_encoder yaml file into a json file (much faster loading)

    cf. https://github.com/emanjavacas/pie/issues/24

    :param input_file:
    :param target_file:
    :return:
    """
    if not target_file:
        target_file = input_file.replace(".tar", "-json.tar")
    label_encoder_path = 'label_encoder.zip'

    _removeFile(input_file, target_file, label_encoder_path)

    with tarfile.open(pie.utils.ensure_ext(input_file, 'tar'), 'r') as tar:
        data = yaml.load(gzip.open(tar.extractfile(label_encoder_path)).read().decode().strip())
    del tar

    shutil.copy(input_file, target_file)
    with tarfile.open(pie.utils.ensure_ext(target_file, 'tar'), 'a') as tar:
        pie.utils.add_gzip_to_tar(json.dumps(data), label_encoder_path, tar)
