import unittest
import yaml
from scenarios import scenario_from_config, repair_topology, ALL_BRANCH_IDS
from fuzzy_poa import optimize
from constraints import graph_properties

class TestReproducibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=yaml.safe_load(open("config.yaml","r",encoding="utf-8"))
        # keep unit test fast while retaining logic
        cls.cfg["population_size"]=8
        cls.cfg["max_iterations"]=4
        cls.cfg["stagnation_window"]=2
        cls.sc=scenario_from_config(cls.cfg,"base")

    def test_topology_repair_is_radial(self):
        scores={idx:(idx%7)/7 for idx in ALL_BRANCH_IDS}
        closed=repair_topology(scores,[])
        connected,radial=graph_properties(closed)
        self.assertTrue(connected)
        self.assertTrue(radial)
        self.assertEqual(len(closed),32)

    def test_same_seed_same_result(self):
        r1=optimize(3,"FC",self.cfg,self.sc,123)
        r2=optimize(3,"FC",self.cfg,self.sc,123)
        self.assertAlmostEqual(r1.best.score,r2.best.score,places=12)
        self.assertEqual(r1.best.closed,r2.best.closed)

    def test_faulted_branch_is_open(self):
        sc=scenario_from_config(self.cfg,"fault_line_7")
        r=optimize(3,"FC",self.cfg,sc,123)
        self.assertNotIn(7,r.best.closed)

if __name__=="__main__":
    unittest.main()
