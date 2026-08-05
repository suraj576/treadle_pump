A treadle pump is an irrigation pump that lifts water by driving a piston through a foot-operated lever. The lever is connected to the rubber piston through a connecting rod.
This device is mainly fabricated in rural and remote areas, where there is usually lack of proper resources such as high end machine tools and skilled manufacturers. As a result of this, the parts built are not as per required fits and tolerances.
The revolute joint between lever and connecting rod is clearance fitted, and the parts fabricated cannot hold a close fit. This results in repeated impacts in the joint, leading to jerks and chattering. This also reduces the output of the pump and thereby impacting the irrigation for farmers.

Since achieving closer fits need high end machinery, a more suitable and economic way is to redistribute the mass of the lever and connecting rod. This changes its dynamic behavior and thus reduces the impact.

Find the mass distribution (centre of mass location and moment of inertia) that minimizes F over one stroke, where e is the separation between the journal and bearing centres and c is the radial clearance.

F = sqrt( mean( (e - c)^2 ) )

Treadle pump geometry, link properties, material data, the applied loads and the stroke definition are in /app/data/pump_specification.yaml. Bore and journal radii are both given; their difference is the radial clearance.

Mass of the links and centre of mass location can be changed within the ranges mentioned in /app/data/design_bounds.csv.

Write to /app/output/:


optimised_design.json with keys: mass_lever, com_lever, mass_rod, com_rod, objective, stroke_duration.
