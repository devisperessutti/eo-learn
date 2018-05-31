import unittest
import logging
import os
import shutil

from eolearn.core.eodata import EOPatch, FeatureType

import numpy as np


logging.basicConfig(level=logging.DEBUG)


class TestEOPatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.mkdir('./test_outputs')

    def test_add_feature(self):
        bands = np.arange(2*3*3*2).reshape(2, 3, 3, 2)

        eop = EOPatch()
        eop.add_feature(attr_type=FeatureType.DATA, field='bands', value=bands)

        self.assertTrue(np.array_equal(eop.data['bands'], bands), msg="Data numpy array not stored")

    def test_get_feature(self):
        bands = np.arange(2*3*3*2).reshape(2, 3, 3, 2)

        eop = EOPatch()
        eop.add_feature(attr_type=FeatureType.DATA, field='bands', value=bands)

        eop_bands = eop.get_feature(FeatureType.DATA, 'bands')

        self.assertTrue(np.array_equal(eop_bands, bands), msg="Data numpy array not returned properly")

    def test_remove_feature(self):
        bands = np.arange(2*3*3*2).reshape(2, 3, 3, 2)

        eop = EOPatch()
        eop.add_feature(attr_type=FeatureType.DATA, field='bands', value=bands)
        eop.add_feature(attr_type=FeatureType.DATA, field='bands_copy', value=bands)

        self.assertTrue('bands_copy' in eop.data.keys(), msg="Data numpy array not stored")
        self.assertTrue('bands_copy' in eop.features[FeatureType.DATA], msg="Feature key not stored")

        eop.remove_feature(attr_type=FeatureType.DATA, field='bands_copy')
        self.assertFalse('bands_copy' in eop.data.keys(), msg="Data numpy array not removed")
        self.assertFalse('bands_copy' in eop.features[FeatureType.DATA], msg="Feature key not removed")
        self.assertTrue('bands' in eop.data.keys(), msg="Data numpy array not stored after removal of other feature")

    def test_check_dims(self):
        bands_2d = np.arange(3*3).reshape(3, 3)
        bands_3d = np.arange(3*3*3).reshape(3, 3, 3)
        with self.assertRaises(ValueError):
            EOPatch(data={'bands': bands_2d})
        eop = EOPatch()
        with self.assertRaises(ValueError):
            eop.add_feature(attr_type=FeatureType.DATA, field='bands', value=bands_2d)
        with self.assertRaises(ValueError):
            eop.add_feature(attr_type=FeatureType.MASK, field='mask', value=bands_2d)
        with self.assertRaises(ValueError):
            eop.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='bands_timeless', value=bands_2d)
        with self.assertRaises(ValueError):
            eop.add_feature(attr_type=FeatureType.MASK_TIMELESS, field='mask_timeless', value=bands_2d)
        with self.assertRaises(ValueError):
            eop.add_feature(attr_type=FeatureType.LABEL, field='label', value=bands_3d)
        with self.assertRaises(ValueError):
            eop.add_feature(attr_type=FeatureType.SCALAR, field='scalar', value=bands_3d)
        with self.assertRaises(ValueError):
            eop.add_feature(attr_type=FeatureType.LABEL_TIMELESS, field='label_timeless', value=bands_2d)
        with self.assertRaises(ValueError):
            eop.add_feature(attr_type=FeatureType.SCALAR_TIMELESS, field='scalar_timeless', value=bands_2d)

    def test_concatenate(self):
        eop1 = EOPatch()
        bands1 = np.arange(2*3*3*2).reshape(2, 3, 3, 2)
        eop1.add_feature(attr_type=FeatureType.DATA, field='bands', value=bands1)

        eop2 = EOPatch()
        bands2 = np.arange(3*3*3*2).reshape(3, 3, 3, 2)
        eop2.add_feature(attr_type=FeatureType.DATA, field='bands', value=bands2)

        eop = EOPatch.concatenate(eop1, eop2)

        self.assertTrue(np.array_equal(eop.data['bands'], np.concatenate((bands1, bands2), axis=0)),
                        msg="Array mismatch")

    def test_get_features(self):
        eop = EOPatch()
        bands1 = np.arange(2*3*3*2).reshape(2, 3, 3, 2)
        eop.add_feature(attr_type=FeatureType.DATA, field='bands', value=bands1)
        self.assertEqual(eop.features[FeatureType.DATA]['bands'], (2, 3, 3, 2))

    def test_concatenate_prohibit_key_mismatch(self):
        eop1 = EOPatch()
        bands1 = np.arange(2*3*3*2).reshape(2, 3, 3, 2)
        eop1.add_feature(attr_type=FeatureType.DATA, field='bands', value=bands1)

        eop2 = EOPatch()
        bands2 = np.arange(3*3*3*2).reshape(3, 3, 3, 2)
        eop2.add_feature(attr_type=FeatureType.DATA, field='measurements', value=bands2)

        with self.assertRaises(ValueError):
            EOPatch.concatenate(eop1, eop2)

    def test_concatenate_leave_out_timeless_mismatched_keys(self):
        eop1 = EOPatch()
        mask1 = np.arange(3*3*2).reshape(3, 3, 2)
        eop1.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='mask1', value=mask1)
        eop1.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='mask', value=5*mask1)

        eop2 = EOPatch()
        mask2 = np.arange(3*3*2).reshape(3, 3, 2)
        eop2.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='mask2', value=mask2)
        eop2.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='mask', value=5*mask1)  # add mask1 to eop2

        eop = EOPatch.concatenate(eop1, eop2)

        self.assertTrue('mask1' not in eop.data_timeless)
        self.assertTrue('mask2' not in eop.data_timeless)

        self.assertTrue('mask' in eop.data_timeless)

    def test_concatenate_leave_out_keys_with_mismatched_value(self):
        mask = np.arange(3*3*2).reshape(3, 3, 2)

        eop1 = EOPatch()
        eop1.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='mask', value=mask)
        eop1.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='nask', value=3*mask)

        eop2 = EOPatch()
        eop2.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='mask', value=mask)
        eop2.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='nask', value=5*mask)

        eop = EOPatch.concatenate(eop1, eop2)

        self.assertTrue('mask' in eop.data_timeless)
        self.assertFalse('nask' in eop.data_timeless)

    def test_equals(self):
        eop1 = EOPatch(data={'bands': np.arange(2*3*3*2).reshape(2, 3, 3, 2)})
        eop2 = EOPatch(data={'bands': np.arange(2*3*3*2).reshape(2, 3, 3, 2)})

        self.assertTrue(eop1 == eop2)

        eop1.add_feature(FeatureType.DATA_TIMELESS, field='dem', value=np.arange(3*3*2).reshape(3, 3, 2))

        self.assertFalse(eop1 == eop2)

    def test_save_load(self):
        eop1 = EOPatch()
        mask1 = np.arange(3*3*2).reshape(3, 3, 2)
        eop1.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='mask1', value=mask1)
        eop1.add_feature(attr_type=FeatureType.DATA_TIMELESS, field='mask', value=5 * mask1)

        eop1.save('./test_outputs/eop1/')

        eop2 = EOPatch.load('./test_outputs/eop1')

        self.assertEqual(eop1, eop2)

    @classmethod
    def tearDown(cls):
        shutil.rmtree('./test_outputs/', ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
