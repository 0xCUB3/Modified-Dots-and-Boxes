use ahash::AHashMap as HashMap;
use std::collections::HashSet;
use std::fs::File;
use std::io::{self, BufRead};
use std::io::Write;
use std::path::Path;
use std::time::Instant;

#[derive(Clone)]
struct Vertex {
    raw_id: usize,
    neighbors: Vec<usize>,
    num_neighbors: usize,
    num_loops: usize,
    canonical_id: isize,
    category_key: Option<Vec<isize>>,
    category: isize,
    prior_category: isize,
}

impl Vertex {
    fn new(raw_id: usize, neighbors: Vec<usize>) -> Self {
        let mut vertex = Vertex {
            raw_id,
            neighbors,
            num_neighbors: 0,
            num_loops: 0,
            canonical_id: -1,
            category_key: None,
            category: -1,
            prior_category: -1,
        };
        vertex.num_neighbors = vertex.neighbors.len();
        vertex.init_num_loops();
        vertex
    }

    fn init_num_loops(&mut self) {
        self.num_loops = self.neighbors.iter().filter(|&&n| n == self.raw_id).count();
    }

    fn add_neighbor(&mut self, neighbor: usize) {
        self.neighbors.push(neighbor);
        self.num_neighbors += 1;
        if neighbor == self.raw_id {
            self.num_loops += 1;
        }
    }
}

struct CanonicalEdges {
    edges: Vec<(usize, usize)>,
    vertices: HashMap<usize, Vertex>,
    num_vertices: usize,
    category_keys: Vec<Vec<isize>>,
    num_categories: usize,
    iterations: usize,
    next_canonical_id: usize,
}

impl CanonicalEdges {
    fn new(edges: Vec<(usize, usize)>) -> Self {
        let mut canonical_edges = CanonicalEdges {
            edges,
            vertices: HashMap::new(),
            num_vertices: 0,
            category_keys: Vec::new(),
            num_categories: 0,
            iterations: 0,
            next_canonical_id: 0,
        };
        canonical_edges.init_vertices();
        canonical_edges
    }

    fn init_vertices(&mut self) {
        for &(v0, v1) in &self.edges {
            self.vertices.entry(v0).or_insert_with(|| Vertex::new(v0, vec![v1])).add_neighbor(v1);
            if v1 != v0 {
                self.vertices.entry(v1).or_insert_with(|| Vertex::new(v1, vec![v0])).add_neighbor(v0);
            }
        }
        self.num_vertices = self.vertices.len();
    }

    fn calc(&mut self) -> Vec<(usize, usize)> {
        self.categorize_vertices_by_connections();
        self.finalize_canonical_ids();
        let mut raw_edges: Vec<(usize, usize)> = Vec::new();
        for v in self.vertices.values() {
            for &n in &v.neighbors {
                if v.canonical_id <= self.vertices[&n].canonical_id {
                    raw_edges.push((v.canonical_id as usize, self.vertices[&n].canonical_id as usize));
                }
            }
        }
        raw_edges.sort();
        raw_edges
    }

    fn categorize_vertices_by_connections(&mut self) {
        self.init_category_iteration_variables();
        while !self.iteration_is_done() {
            self.update_category_iteration_variables();
        }
    }

    fn init_category_iteration_variables(&mut self) {
        self.iterations = 0;
        for v in self.vertices.values_mut() {
            v.category_key = Some(vec![v.num_neighbors as isize, -1 * v.num_loops as isize]);
        }
        self.update_categories_based_on_category_keys();
    }

    fn update_categories_based_on_category_keys(&mut self) {
        let mut category_keys_set: HashSet<Vec<isize>> = HashSet::new();
        for v in self.vertices.values() {
            category_keys_set.insert(v.category_key.clone().unwrap());
        }
        self.category_keys = category_keys_set.into_iter().collect();
        self.category_keys.sort();
        self.num_categories = self.category_keys.len();
        let mut vertices_for_category_key: HashMap<Vec<isize>, Vec<&mut Vertex>> = HashMap::new();
        for v in self.vertices.values_mut() {
            vertices_for_category_key.entry(v.category_key.clone().unwrap()).or_insert_with(Vec::new).push(v);
        }
        for (i, category_key) in self.category_keys.iter().enumerate() {
            for v in vertices_for_category_key.get_mut(category_key).unwrap() {
                v.category = i as isize;
            }
        }
        self.iterations += 1;
    }

    fn iteration_is_done(&self) -> bool {
        let done_for_simple_cases = self.num_categories == 1
            || self.num_categories == self.num_vertices
            || self.iterations >= self.num_vertices;
        if done_for_simple_cases {
            true
        } else {
            !self.vertices.values().any(|v| v.category != v.prior_category)
        }
    }

    fn update_category_iteration_variables(&mut self) {
        let mut num_neighbors_for_category_vec: Vec<Vec<isize>> = Vec::new();
        for v in self.vertices.values() {
            let mut num_neighbors_for_category = vec![0; self.num_categories];
            for &n in &v.neighbors {
                num_neighbors_for_category[self.vertices[&n].category as usize] += 1;
            }
            num_neighbors_for_category_vec.push(num_neighbors_for_category.into_iter().map(|x| x as isize).collect());
        }
    
        for (v, num_neighbors_for_category) in self.vertices.values_mut().zip(num_neighbors_for_category_vec) {
            v.prior_category = v.category;
            v.category_key = Some(vec![v.category]);
            v.category_key.as_mut().unwrap().extend(num_neighbors_for_category.iter().cloned().rev());
        }
    
        self.update_categories_based_on_category_keys();
    }

    fn finalize_canonical_ids(&mut self) {
        if self.num_categories == self.num_vertices {
            for v in self.vertices.values_mut() {
                v.canonical_id = v.category;
            }
        } else {
            let mut vertices_for_category: HashMap<isize, Vec<*mut Vertex>> = HashMap::new();
            for v in self.vertices.values_mut() {
                vertices_for_category.entry(v.category).or_insert_with(Vec::new).push(v as *mut Vertex);
            }
            self.next_canonical_id = 0;
            for i in 0..self.num_categories {
                if let Some(category_vertices) = vertices_for_category.get_mut(&(i as isize)) {
                    let mut category_vertices_refs: Vec<&mut Vertex> = category_vertices.iter_mut().map(|&mut v| unsafe { &mut *v }).collect();
                    self.assign_canonical_ids_for_ties(&mut category_vertices_refs);
                }
            }
        }
    }

    fn assign_canonical_ids_for_ties(&mut self, vertices: &mut Vec<&mut Vertex>) {
        while !vertices.is_empty() {
            let next_vertex_index = if vertices.len() == 1 {
                0
            } else {
                let mut connected: Vec<usize> = Vec::new();
                let mut not_connected: Vec<usize> = Vec::new();
    
                for (i, v) in vertices.iter_mut().enumerate() {
                    if v.neighbors.iter().any(|&n| self.vertices[&n].canonical_id != -1) {
                        connected.push(i);
                    } else {
                        not_connected.push(i);
                    }
                }
    
                if !connected.is_empty() {
                    let mut min_canonical_id: HashMap<usize, isize> = connected.iter().map(|&i| (vertices[i].raw_id, self.num_vertices as isize)).collect();
                    for &i in &connected {
                        let v = &vertices[i];
                        for &n in &v.neighbors {
                            if self.vertices[&n].canonical_id != -1 {
                                if self.vertices[&n].canonical_id < min_canonical_id[&v.raw_id] {
                                    min_canonical_id.insert(v.raw_id, self.vertices[&n].canonical_id);
                                }
                            }
                        }
                    }
                    *connected.iter().min_by_key(|&&i| (min_canonical_id[&vertices[i].raw_id], vertices[i].raw_id)).unwrap()
                } else {
                    *not_connected.iter().min_by_key(|&&i| vertices[i].raw_id).unwrap()
                }
            };
    
            let next_vertex = &mut vertices[next_vertex_index];
            next_vertex.canonical_id = self.next_canonical_id as isize;
            self.next_canonical_id += 1;
            vertices.remove(next_vertex_index);
        }
    }
}

fn edges_from_input_file() -> io::Result<Vec<(usize, usize)>> {
    let path = Path::new("game_input.txt");
    let file = File::open(&path)?;
    let lines = io::BufReader::new(file).lines();
    let mut edges = Vec::new();
    for line in lines {
        let line = line?;
        let vertices: Vec<&str> = line.split(',').collect();
        edges.push((vertices[0].parse().unwrap(), vertices[1].parse().unwrap()));
    }
    Ok(edges)
}

fn edges_for_m_by_n_grid(m: usize, n: usize) -> Vec<(usize, usize)> {
    let mut edges = Vec::new();
    for i in 0..m {
        for j in 0..n {
            let vertex = i * n + j;
            if i == 0 || i == m - 1 {
                edges.push((vertex, vertex));
            } else {
                edges.push((vertex, vertex + n));
            }
            if j == 0 || j == n - 1 {
                edges.push((vertex, vertex));
            } else {
                edges.push((vertex, vertex + 1));
            }
        }
    }
    edges
}

fn edges_for_complete_graph(n: usize) -> Vec<(usize, usize)> {
    let mut edges = Vec::new();
    for i in 0..n - 1 {
        for j in i + 1..n {
            edges.push((i, j));
        }
    }
    edges
}

fn edges_for_wheel(n: usize) -> Vec<(usize, usize)> {
    let mut edges = Vec::new();
    for i in 0..n - 1 {
        edges.push((i, i + 1));
        edges.push((i, n));
    }
    edges.push((n - 1, 0));
    edges.push((n - 1, n));
    edges
}

struct GameGraph {
    edges: Vec<(usize, usize)>,
    vertices: HashSet<usize>,
    num_edges: usize,
    num_vertices: usize,
    have_set_key: bool,
    have_determined_if_is_tree: bool,
    key: String,
    is_tree: bool,
    tree_edges: Vec<(usize, usize)>,
    num_edges_for_tree_vertex: HashMap<usize, usize>,
    tree_ends: Vec<usize>,
}

impl GameGraph {
    fn new(edges: Vec<(usize, usize)>) -> Self {
        let vertices: HashSet<usize> = edges.iter().flat_map(|&(a, b)| vec![a, b]).collect();
        let num_edges = edges.len();
        let num_vertices = vertices.len();
        GameGraph {
            edges,
            vertices,
            num_edges,
            num_vertices,
            have_set_key: false,
            have_determined_if_is_tree: false,
            key: String::new(),
            is_tree: false,
            tree_edges: Vec::new(),
            num_edges_for_tree_vertex: HashMap::new(),
            tree_ends: Vec::new(),
        }
    }

    fn contains_vertex(&self, vertex: usize) -> bool {
        self.vertices.contains(&vertex)
    }

    fn get_key(&mut self) -> &str {
        if !self.have_set_key {
            let canonical_edges = CanonicalEdges::new(self.edges.clone()).calc();
            self.key = canonical_edges.iter().map(|&(a, b)| format!("{}-{}", a, b)).collect::<Vec<String>>().join("|");
            self.have_set_key = true;
        }
        &self.key
    }

    fn is_tree(&mut self) -> bool {
        if !self.have_determined_if_is_tree {
            if self.num_edges > self.num_vertices {
                self.is_tree = false;
            } else if self.num_edges == 1 {
                self.is_tree = true;
            } else {
                self.iteratively_pare_tree();
                self.is_tree = self.tree_edges.is_empty();
            }
            self.have_determined_if_is_tree = true;
        }
        self.is_tree
    }

    fn iteratively_pare_tree(&mut self) {
        self.initialize_tree_attributes();
        while !self.tree_ends.is_empty() {
            self.remove_ends_from_tree();
        }
    }

    fn initialize_tree_attributes(&mut self) {
        self.tree_edges = self.edges.clone();
        self.num_edges_for_tree_vertex = self.vertices.iter().map(|&v| (v, 0)).collect();
        for &(a, b) in &self.tree_edges {
            *self.num_edges_for_tree_vertex.get_mut(&a).unwrap() += 1;
            if a != b {
                *self.num_edges_for_tree_vertex.get_mut(&b).unwrap() += 1;
            }
        }
        self.update_tree_ends();
    }

    fn update_tree_ends(&mut self) {
        self.tree_ends = self.num_edges_for_tree_vertex.iter().filter_map(|(&v, &num)| if num == 1 { Some(v) } else { None }).collect();
    }

    fn remove_ends_from_tree(&mut self) {
        for &(a, b) in &self.tree_edges.clone() {
            if self.tree_ends.contains(&a) || self.tree_ends.contains(&b) {
                self.decrement_num_edges_for_tree_vertex(a);
                if a != b {
                    self.decrement_num_edges_for_tree_vertex(b);
                }
                self.tree_edges.retain(|&(x, y)| x != a || y != b);
            }
        }
        self.update_tree_ends();
    }

    fn decrement_num_edges_for_tree_vertex(&mut self, vertex: usize) {
        if let Some(num) = self.num_edges_for_tree_vertex.get_mut(&vertex) {
            *num -= 1;
            if *num == 0 {
                self.num_edges_for_tree_vertex.remove(&vertex);
            }
        }
    }
}

impl Default for GameGraph {
    fn default() -> Self {
        GameGraph {
            edges: Vec::new(),
            vertices: HashSet::new(),
            num_edges: 0,
            num_vertices: 0,
            have_set_key: false,
            have_determined_if_is_tree: false,
            key: String::new(),
            is_tree: false,
            tree_edges: Vec::new(),
            num_edges_for_tree_vertex: HashMap::new(),
            tree_ends: Vec::new(),
        }
    }
}

struct GameRunner {
    edges: Vec<(usize, usize)>,
    initial_graph: GameGraph,
    memo: HashMap<String, isize>,
    progress: Progress,
}

struct Progress {
    top_level: usize,
    count: usize,
    start_time: Instant,
}

impl GameRunner {
    fn new(edges: Vec<(usize, usize)>) -> Self {
        let initial_graph = GameGraph::new(edges.clone());
        let num_edges = initial_graph.num_edges; // Clone the necessary field before moving
        GameRunner {
            edges,
            initial_graph,
            memo: HashMap::new(),
            progress: Progress {
                top_level: num_edges,
                count: 0,
                start_time: Instant::now(),
            },
        }
    }

    fn run(&mut self, write_file: bool) -> isize {
        self.init_memo();
        
        // Temporarily take ownership of initial_graph
        let mut initial_graph = std::mem::take(&mut self.initial_graph);
        
        // Calculate net_score
        let net_score = self.net_score(&mut initial_graph, 0);
        
        // Put initial_graph back into self
        self.initial_graph = initial_graph;
        
        // Print the result
        if net_score == 0 {
            println!("Tie game.");
        } else {
            let winner = if net_score > 0 { "P1" } else { "P2" };
            println!("{} wins with a net score of {} (P1-P2).", winner, net_score);
        }
        
        // Write memo if needed
        if write_file {
            self.write_memo();
        }
        
        net_score
    }

    fn init_memo(&mut self) {
        if let Ok(file) = File::open("net_scores.txt") {
            for line in io::BufReader::new(file).lines() {
                if let Ok(line) = line {
                    let items: Vec<&str> = line.split(',').collect();
                    self.memo.insert(items[0].to_string(), items[1].parse().unwrap());
                }
            }
        }
    }

    fn write_memo(&self) {
        if let Ok(mut file) = File::create("net_scores.txt") {
            for (key, value) in &self.memo {
                writeln!(file, "{},{}", key, value).unwrap();
            }
        }
    }

    fn net_score(&mut self, graph: &mut GameGraph, depth: usize) -> isize {
        let key = graph.get_key().to_string();
        if let Some(&score) = self.memo.get(&key) {
            return score;
        }
        if graph.is_tree() {
            let score = graph.num_vertices as isize;
            self.memo.insert(key, score);
            return score;
        }
        let new_depth = depth + 1;
        let mut best_outcome = -1 * graph.num_vertices as isize;
        let mut tried_edges = HashSet::new();
        for &e in &graph.edges {
            if tried_edges.contains(&e) {
                continue;
            }
            tried_edges.insert(e);
            let (mut new_graph, points) = self.cut_edge(graph, e);
            let mult = if points > 0 { 1 } else { -1 };
            let outcome = points + mult * self.net_score(&mut new_graph, new_depth);
            if outcome > best_outcome {
                best_outcome = outcome;
                if outcome == graph.num_vertices as isize {
                    break;
                }
            }
        }
        self.track_progress(depth);
        self.memo.insert(key, best_outcome);
        best_outcome
    }

    fn cut_edge(&self, graph: &GameGraph, edge: (usize, usize)) -> (GameGraph, isize) {
        let mut new_edges = graph.edges.clone();
        new_edges.retain(|&e| e != edge);
        let new_graph = GameGraph::new(new_edges);
        let mut points = 0;
        if !new_graph.contains_vertex(edge.0) {
            points += 1;
        }
        if edge.1 != edge.0 && !new_graph.contains_vertex(edge.1) {
            points += 1;
        }
        (new_graph, points)
    }

    fn track_progress(&mut self, depth: usize) {
        if depth <= self.progress.top_level {
            if depth == self.progress.top_level {
                self.progress.count += 1;
            } else {
                self.progress.top_level = depth;
                self.progress.count = 1;
            }
            let elapsed_secs = self.progress.start_time.elapsed().as_secs_f64();
            println!(
                "top solved depth:{} count:{} seconds:{:.2}",
                depth, self.progress.count, elapsed_secs
            );
        }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let src_type = args.get(1).map(|s| s.as_str()).unwrap_or("file");
    let params: Vec<usize> = args.iter().skip(2).filter_map(|s| s.parse().ok()).collect();
    let save_memo = args.contains(&"--save_memo".to_string());

    let edges = match src_type {
        "file" => edges_from_input_file().unwrap(),
        "m_by_n" => edges_for_m_by_n_grid(params[0], params[1]),
        "complete" => edges_for_complete_graph(params[0]),
        "wheel" => edges_for_wheel(params[0]),
        _ => panic!("Unrecognized edge source type: {}", src_type),
    };

    let mut game_runner = GameRunner::new(edges);
    game_runner.run(save_memo);
}