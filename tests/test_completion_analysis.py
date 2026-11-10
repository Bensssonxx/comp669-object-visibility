"""Tests for statistical units and paired estimates, independent of model inference."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_completion import ImageBootstrap,bins,image_average


class BootstrapTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({'image_id':['a','b','c','d'],'label':[0,0,1,1],
                             'aimv2':[1.,0.,1.,0.],'dinov2':[1.,0.,1.,0.]})

    def test_identical_models_have_exact_zero_paired_difference(self):
        f=self.frame();point,ci,draws,_=ImageBootstrap(f,500).estimate(f)
        self.assertEqual(point[2],0)
        np.testing.assert_array_equal(draws[:,2],0)
        np.testing.assert_array_equal(ci[:,2],0)

    def test_repeated_versions_are_not_independent_bootstrap_units(self):
        f=self.frame();b=ImageBootstrap(f,500)
        original=b.estimate(f)
        repeated=pd.concat([f,f,f],ignore_index=True)
        actual=b.estimate(repeated,np.full(12,1/3))
        np.testing.assert_allclose(actual[2],original[2],atol=1e-14)
        self.assertEqual(len(b.ids),4)

    def test_equal_breed_and_image_weighting_are_distinct(self):
        f=pd.DataFrame({'image_id':['a','b','c','d'],'label':[0,0,0,1],
                        'aimv2':[1.,1.,1.,0.],'dinov2':[0.,0.,0.,0.]})
        b=ImageBootstrap(f,100)
        self.assertAlmostEqual(b.estimate(f)[0][0],.75)
        self.assertAlmostEqual(b.estimate(f,equal_breed=True)[0][0],.5)

    def test_sparse_bins_do_not_report_accuracy(self):
        f=self.frame().assign(cohort='test',fraction=.25,fill=128,pattern='center',object_visibility=.3)
        result=bins(f,ImageBootstrap(f,100),.2)
        self.assertTrue(result.estimate.isna().all())
        self.assertTrue((result.n_images==4).all())

    def test_full_visibility_included_in_last_bin(self):
        f=pd.DataFrame({'image_id':list('abcdef'),'label':[0]*6,'aimv2':[1.]*6,'dinov2':[0.]*6})
        f=f.assign(cohort='test',fraction=.75,fill=128,pattern='center',object_visibility=1.)
        result=bins(f,ImageBootstrap(f,100),.2)
        self.assertTrue((result.fg_bin==4).all())
        self.assertEqual(result[result.metric=='aimv2'].estimate.iloc[0],1.)

    def test_exact_internal_boundaries_enter_upper_interval(self):
        f=pd.DataFrame({'image_id':[str(i) for i in range(25)],'label':[0]*25,
                        'aimv2':[1.]*25,'dinov2':[0.]*25,'object_visibility':np.repeat([.2,.4,.6,.8,1.],5)})
        f=f.assign(cohort='test',fraction=.75,fill=128,pattern='center')
        result=bins(f,ImageBootstrap(f,100),.2)
        actual=result[result.metric=='aimv2'].set_index('fg_bin').n_images.to_dict()
        self.assertEqual(actual,{1:5,2:5,3:5,4:10})

    def test_visibility_budgets_never_collapse_during_repeat_average(self):
        f=pd.concat([self.frame().assign(fraction=.25),self.frame().assign(fraction=.75)],ignore_index=True)
        f=f.assign(cohort='test',fill=128,pattern='random',suite='standard',object_visibility=.5,
                   background_visibility=.5,head_visibility=np.nan,body_visibility=np.nan,head_foreground_fraction=np.nan)
        result=image_average(f)
        self.assertEqual(len(result),8)
        self.assertEqual(set(result.fraction),{.25,.75})


if __name__=='__main__':unittest.main()
