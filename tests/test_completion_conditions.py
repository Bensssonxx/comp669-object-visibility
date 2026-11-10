"""Ensure the budget extension cannot silently collide conditions or change inputs."""
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import complete_occlusion as completion
from occlusion_visibility.experiment import decode_mask


class ConditionsTests(unittest.TestCase):
    def rows(self):
        rgb=np.zeros((224,224,3),dtype=np.uint8)
        trimap=np.full((224,224),2,dtype=np.uint8);trimap[40:180,60:160]=1
        config={'fractions':[.5,.75],'fills':[128,0]}
        manifest=[{'image_id':'synthetic','label':0,'cohort':'primary'}]
        with patch.object(completion,'load_image',return_value=(rgb,trimap)):
            return completion.conditions(manifest,config)[0]

    def test_budget_is_part_of_condition_identity(self):
        rows=self.rows()
        self.assertEqual(len(rows),24)
        self.assertEqual(len({r['condition_id'] for r in rows}),24)

    def test_fill_changes_preserve_mask_and_coverage(self):
        rows=self.rows()
        for a,b in zip(rows[::2],rows[1::2]):
            self.assertEqual(a['mask_hex'],b['mask_hex'])
            self.assertEqual(a['object_visibility'],b['object_visibility'])
            self.assertEqual((a['fill'],b['fill']),(128,0))

    def test_nested_masks_and_exact_budgets(self):
        rows=self.rows()
        for pattern in ['prefix','suffix','center','random']:
            a=next(r for r in rows if r['pattern']==pattern and r['fraction']==.5)
            b=next(r for r in rows if r['pattern']==pattern and r['fraction']==.75)
            am=decode_mask(a['mask_hex'],224,14);bm=decode_mask(b['mask_hex'],224,14)
            self.assertEqual(am.mean(),.5);self.assertEqual(bm.mean(),.75)
            self.assertFalse((am&~bm).any())

    def test_generation_is_deterministic(self):self.assertEqual(self.rows(),self.rows())


if __name__=='__main__':unittest.main()
