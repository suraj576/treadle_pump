The overall dimensions and details of the treadle pump is given in 'pump_specification.yaml'. Geometrical details such as link lengths, joint distances, stroke lengths along with forces and torques are mentioned.
The joint clearance between the lever and connecting rod is modeled as a hertzian elastic contact model. This is a standard contact model used in clearance dyanmics.
Equations of motion for the systems is derived using newton-ruler formulation. The differential equations are solved using a fixed step range-kutta solver. 
For optimization, the objective is to minimize the root mean square of the pin to bore center offset distance over a complete stroke.

Six design variables are mentioned for the optimization. Particle swarm optimization is used since it is computationally efficient. It is also made sure that the obtained value is not a local optima by introducing disturbances.

Verification check:
A reference model runs the design variables and recomputes the objective function. This makes sure that both the physics (multi body dynamics) and the optimization is verified.
