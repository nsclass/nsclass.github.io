---
layout: single
title: C++ - Practical Data-Oriented Design
date: 2026-02-22 19:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2026/02/22/cpp-data-oriented-design"
---
[More Speed & Simplicity: Practical Data-Oriented Design in C++ - Vittorio Romeo - CppCon 2025](https://www.youtube.com/watch?v=SzjJfKHygaQ)

### Data-Oriented Design (DOD)

Data-Oriented Design (DOD) is a programming paradigm that prioritizes the layout and access patterns of data in memory to maximize performance, particularly through CPU cache efficiency. While Object-Oriented Programming (OOP) focuses on encapsulation and object behavior, DOD focuses on how data is transformed.

### OOP Approach: Array-of-Structures (AoS)

In the traditional OOP approach, we model our game world with a `World` class that manages a collection of `Entity` objects using polymorphism.

```cpp
class Entity {
public:
    virtual ~Entity() = default;
    virtual void update(float dt) = 0;
};

class Rocket : public Entity {
    vec3 pos, vel;
    Emitter emitter; // Rocket "owns" an emitter
public:
    void update(float dt) override {
        pos += vel * dt;
        emitter.update(dt, pos); // Spawns particles
    }
};

class Particle : public Entity {
    vec3 pos, vel;
public:
    void update(float dt) override { pos += vel * dt; }
};

class World {
    std::vector<std::unique_ptr<Entity>> entities;
public:
    void update(float dt) {
        for(auto& e : entities) e->update(dt);
    }
};
```

### DOD Approach: Structure-of-Arrays (SoA) & Bulk Processing

In DOD, we flatten the hierarchy. The `World` owns separate, contiguous arrays of data, and we process them in bulk.

```cpp
struct Rocket { vec3 pos, vel; };
struct Particle { vec3 pos, vel; };
struct Emitter { vec3 pos; /* ... */ };

class World {
    std::vector<Rocket> rockets;
    std::vector<Particle> particles;
    std::vector<Emitter> emitters;

public:
    void update(float dt) {
        // 1. Update all rockets (contiguous memory access)
        for(auto& r : rockets) r.pos += r.vel * dt;

        // 2. Update all emitters (could be linked to rockets by index)
        for(size_t i = 0; i < emitters.size(); ++i) {
            emitters[i].pos = rockets[i].pos;
            emitters[i].emit(particles);
        }

        // 3. Update all particles (bulk processing)
        for(auto& p : particles) p.pos += p.vel * dt;
    }
};
```

### Practical DOD Examples

#### 1. Cache Locality (Hot/Cold Splitting)
By maintaining separate vectors in the `World` object, we ensure that during the particle update loop, *only* particle data is in the cache. In the OOP approach, the cache would be polluted with vtable pointers and other entity data.

```cpp
// Hot data: Processed every frame in bulk
std::vector<Particle> active_particles; 

// Cold data: Only used for infrequent logic (e.g. debugging/UI)
struct ParticleDebugInfo { std::string source_rocket_name; };
std::vector<ParticleDebugInfo> debug_info;
```

#### 2. Extensibility
In the OOP `World`, adding a `Shield` entity requires inheriting from `Entity`. In DOD, we just add `std::vector<Shield> shields` to the `World` and a new loop in `update()`. This avoids the "Fragile Base Class" problem.

```cpp
struct Shield { vec3 pos; float radius; };

void World::update(float dt) {
    // ... other updates ...
    for(auto& s : shields) s.radius -= dt; // Easy to add new logic
}
```

#### 3. Testability
Since `update_particles` doesn't depend on the state of a `World` object or a `Rocket` object, we can test it by just passing a vector of data.

```cpp
void update_particles(std::span<Particle> particles, float dt) {
    for(auto& p : particles) p.pos += p.vel * dt;
}

// Test:
std::vector<Particle> test_particles = {{ {0,0,0}, {1,0,0} }};
update_particles(test_particles, 1.0f);
assert(test_particles[0].pos.x == 1.0f);
```

#### 4. Multi-threading Support
Because the `World` stores rockets and particles in separate, independent vectors, we can update them in parallel without any synchronization (mutexes).

```cpp
void World::update(float dt) {
    std::for_each(std::execution::par, rockets.begin(), rockets.end(), 
        [dt](auto& r) { r.pos += r.vel * dt; });
        
    std::for_each(std::execution::par, particles.begin(), particles.end(), 
        [dt](auto& p) { p.pos += p.vel * dt; });
}
```


### Key Takeaways from Vittorio's Talk

1.  **Cache Locality:** Modern CPUs are much faster than memory. Performance is often bound by how quickly we can get data into the cache. Contiguous data access (SoA) is key.
2.  **Simplicity:** DOD often leads to simpler "flat" code where transformations are explicit, rather than hidden behind layers of inheritance and virtual calls.
3.  **Mechanical Sympathy:** Designing software with the hardware's architecture in mind (like the cache line size) yields massive performance gains without complex algorithms.
4.  **Composition over Inheritance:** DOD naturally favors composing data in a way that suits the processing pipeline rather than modeling hierarchical relationships.
