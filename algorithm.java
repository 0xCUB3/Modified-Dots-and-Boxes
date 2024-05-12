import java.util.*;
import java.io.*;

class Vertex {
    int rawId;
    List<Integer> neighbors;
    int numNeighbors;
    int numLoops;
    int canonicalId;
    List<Integer> categoryKey;
    int category;
    int priorCategory;

    Vertex(int rawId, List<Integer> neighbors) {
        this.rawId = rawId;
        this.neighbors = neighbors;
        this.numNeighbors = neighbors.size();
        initNumLoops();
        this.canonicalId = -1;
        this.categoryKey = null;
        this.category = -1;
        this.priorCategory = -1;
    }

    void initNumLoops() {
        numLoops = 0;
        for (int n : neighbors) {
            if (n == rawId) {
                numLoops++;
            }
        }
    }

    void addNeighbor(int neighbor) {
        neighbors.add(neighbor);
        numNeighbors++;
        if (neighbor == rawId) {
            numLoops++;
        }
    }
}

class CanonicalEdges {
    List<List<Integer>> edges;
    Map<Integer, Vertex> vertices;
    int numVertices;
    List<List<Integer>> categoryKeys;
    int numCategories;
    int iterations;
    int nextCanonicalId;

    CanonicalEdges(List<List<Integer>> edges) {
        this.edges = edges;
        initVertices();
    }

    void initVertices() {
        vertices = new HashMap<>();
        for (List<Integer> edge : edges) {
            int v0 = edge.get(0);
            int v1 = edge.get(1);
            if (!vertices.containsKey(v0)) {
                vertices.put(v0, new Vertex(v0, new ArrayList<>(List.of(v1))));
            } else {
                vertices.get(v0).addNeighbor(v1);
            }
            if (v1 != v0) {
                if (!vertices.containsKey(v1)) {
                    vertices.put(v1, new Vertex(v1, new ArrayList<>(List.of(v0))));
                } else {
                    vertices.get(v1).addNeighbor(v0);
                }
            }
        }
        numVertices = vertices.size();
    }

    List<List<Integer>> calc() {
        categorizeVerticesByConnections();
        finalizeCanonicalIds();
        List<List<Integer>> rawEdges = new ArrayList<>();
        for (Vertex v : vertices.values()) {
            for (int n : v.neighbors) {
                if (v.canonicalId <= vertices.get(n).canonicalId) {
                    rawEdges.add(List.of(v.canonicalId, vertices.get(n).canonicalId));
                }
            }
        }
        Collections.sort(rawEdges, Comparator.comparingInt(edge -> edge.get(0)));
        return rawEdges;
    }

    void categorizeVerticesByConnections() {
        initCategoryIterationVariables();
        while (!iterationIsDone()) {
            updateCategoryIterationVariables();
        }
    }

    void initCategoryIterationVariables() {
        iterations = 0;
        for (Vertex v : vertices.values()) {
            v.categoryKey = new ArrayList<>(List.of(v.numNeighbors, -1 * v.numLoops));
        }
        updateCategoriesBasedOnCategoryKeys();
    }

    void updateCategoriesBasedOnCategoryKeys() {
        Set<List<Integer>> keySet = new HashSet<>();
        for (Vertex v : vertices.values()) {
            keySet.add(new ArrayList<>(v.categoryKey));
        }
        categoryKeys = new ArrayList<>(keySet);
        Collections.sort(categoryKeys, Comparator.comparingInt(key -> key.get(0)));
        numCategories = categoryKeys.size();
        Map<List<Integer>, List<Vertex>> verticesForCategoryKey = new HashMap<>();
        for (List<Integer> key : categoryKeys) {
            verticesForCategoryKey.put(key, new ArrayList<>());
        }
        for (Vertex v : vertices.values()) {
            verticesForCategoryKey.get(v.categoryKey).add(v);
        }
        for (int i = 0; i < numCategories; i++) {
            for (Vertex v : verticesForCategoryKey.get(categoryKeys.get(i))) {
                v.category = i;
            }
        }
        iterations++;
    }

    boolean iterationIsDone() {
        boolean doneForSimpleCases = (numCategories == 1) || (numCategories == numVertices) || (iterations >= numVertices);
        if (doneForSimpleCases) {
            return true;
        } else {
            for (Vertex v : vertices.values()) {
                if (v.category != v.priorCategory) {
                    return false;
                }
            }
            return true;
        }
    }

    void updateCategoryIterationVariables() {
        for (Vertex v : vertices.values()) {
            v.priorCategory = v.category;
            v.categoryKey = new ArrayList<>(List.of(v.category));
            int[] numNeighborsForCategory = new int[numCategories];
            for (int n : v.neighbors) {
                numNeighborsForCategory[vertices.get(n).category]++;
            }
            for (int i = numCategories - 1; i >= 0; i--) {
                v.categoryKey.add(numNeighborsForCategory[i]);
            }
        }
        updateCategoriesBasedOnCategoryKeys();
    }

    void finalizeCanonicalIds() {
        if (numCategories == numVertices) {
            for (Vertex v : vertices.values()) {
                v.canonicalId = v.category;
            }
        } else {
            Map<Integer, List<Vertex>> verticesForCategory = new HashMap<>();
            for (int i = 0; i < numCategories; i++) {
                verticesForCategory.put(i, new ArrayList<>());
            }
            for (Vertex v : vertices.values()) {
                verticesForCategory.get(v.category).add(v);
            }
            nextCanonicalId = 0;
            for (int i = 0; i < numCategories; i++) {
                assignCanonicalIdsForTies(verticesForCategory.get(i));
            }
        }
    }

    void assignCanonicalIdsForTies(List<Vertex> vertices) {
        while (!vertices.isEmpty()) {
            Vertex nextVertex;
            if (vertices.size() == 1) {
                nextVertex = vertices.get(0);
            } else {
                List<Vertex> connectedToCanonicalId = new ArrayList<>();
                List<Vertex> notConnectedToCanonicalId = new ArrayList<>();
                splitByConnectionToCanonicalId(vertices, connectedToCanonicalId, notConnectedToCanonicalId);

                if (!connectedToCanonicalId.isEmpty()) {
                    Map<Integer, Integer> minCanonicalId = new HashMap<>();
                    for (Vertex v : connectedToCanonicalId) {
                        minCanonicalId.put(v.rawId, numVertices);
                    }
                    for (Vertex v : connectedToCanonicalId) {
                        for (int n : v.neighbors) {
                            if (vertices.get(n).canonicalId != -1) {
                                minCanonicalId.put(v.rawId, Math.min(minCanonicalId.get(v.rawId), vertices.get(n).canonicalId));
                            }
                        }
                    }
                    connectedToCanonicalId.sort(Comparator.comparingInt((Vertex v) -> minCanonicalId.get(v.rawId))
                            .thenComparingInt(v -> v.rawId));
                    nextVertex = connectedToCanonicalId.get(0);
                } else {
                    notConnectedToCanonicalId.sort(Comparator.comparingInt(v -> v.rawId));
                    nextVertex = notConnectedToCanonicalId.get(0); 
                }
            }
            nextVertex.canonicalId = nextCanonicalId;
            nextCanonicalId++;
            vertices.remove(nextVertex);
        }
    }

    void splitByConnectionToCanonicalId(List<Vertex> vertices,
                                    List<Vertex> connectedToCanonicalId,
                                    List<Vertex> notConnectedToCanonicalId) {

        for (Vertex v : vertices) {
            boolean connected = false;
            for (int n : v.neighbors) {
                if (n >= 0 && n < vertices.size()) {
                    Vertex neighbor = vertices.get(n);
                    if (neighbor.canonicalId != -1) {
                        connectedToCanonicalId.add(v);
                        connected = true;
                        break;
                    }
                }
            }
            if (!connected) {
                notConnectedToCanonicalId.add(v);
            }
        }
    }
}

class GameGraph {
    List<List<Integer>> edges;
    List<Integer> vertices;
    int numEdges;
    int numVertices;
    boolean haveSetKey;
    boolean haveDeterminedIfIsTree;
    String key;
    boolean isTree;
    List<List<Integer>> treeEdges;
    Map<Integer, Integer> numEdgesForTreeVertex;
    List<Integer> treeEnds;

    GameGraph(List<List<Integer>> edges) {
        this.edges = edges;
        this.vertices = vertices();
        this.numEdges = edges.size();
        this.numVertices = vertices.size();
        this.haveSetKey = false;
        this.haveDeterminedIfIsTree = false;
    }

    List<Integer> vertices() {
        Set<Integer> vertexSet = new HashSet<>();
        for (List<Integer> edge : edges) {
            vertexSet.add(edge.get(0));
            vertexSet.add(edge.get(1));
        }
        return new ArrayList<>(vertexSet);
    }

    boolean containsVertex(int vertex) {
        return vertices.contains(vertex);
    }

    String getKey() {
        if (!haveSetKey) {
            key = keyForEdges(new CanonicalEdges(edges).calc());
            haveSetKey = true;
        }
        return key;
    }

    String keyForEdges(List<List<Integer>> edges) {
        List<String> edgeStrs = new ArrayList<>();
        for (List<Integer> edge : edges) {
            edgeStrs.add(edge.get(0) + "-" + edge.get(1));
        }
        return String.join("|", edgeStrs);
    }

    boolean isTree() {
        if (!haveDeterminedIfIsTree) {
            if (numEdges > numVertices) {
                isTree = false;
            } else if (numEdges == 1) {
                isTree = true;
            } else {
                iterativelyPareTree();
                isTree = treeEdges.isEmpty();
            }
            haveDeterminedIfIsTree = true;
        }
        return isTree;
    }

    void iterativelyPareTree() {
        initializeTreeAttributes();
        while (!treeEnds.isEmpty()) {
            removeEndsFromTree();
        }
    }

    void initializeTreeAttributes() {
        treeEdges = new ArrayList<>(edges);
        numEdgesForTreeVertex = new HashMap<>();
        for (int vertex : vertices) {
            numEdgesForTreeVertex.put(vertex, 0);
        }
        for (List<Integer> edge : treeEdges) {
            numEdgesForTreeVertex.put(edge.get(0), numEdgesForTreeVertex.get(edge.get(0)) + 1);
            if (edge.get(1) != edge.get(0)) {
                numEdgesForTreeVertex.put(edge.get(1), numEdgesForTreeVertex.get(edge.get(1)) + 1);
            }
        }
        updateTreeEnds();
    }

    void updateTreeEnds() {
        treeEnds = new ArrayList<>();
        for (Map.Entry<Integer, Integer> entry : numEdgesForTreeVertex.entrySet()) {
            if (entry.getValue() == 1) {
                treeEnds.add(entry.getKey());
            }
        }
    }

    void removeEndsFromTree() {
        for (Iterator<List<Integer>> iterator = treeEdges.iterator(); iterator.hasNext(); ) {
            List<Integer> edge = iterator.next();
            if (treeEnds.contains(edge.get(0)) || treeEnds.contains(edge.get(1))) {
                decrementNumEdgesForTreeVertex(edge.get(0));
                if (edge.get(1) != edge.get(0)) {
                    decrementNumEdgesForTreeVertex(edge.get(1));
                }
                iterator.remove();
            }
        }
        updateTreeEnds();
    }

    void decrementNumEdgesForTreeVertex(int vertex) {
        numEdgesForTreeVertex.put(vertex, numEdgesForTreeVertex.get(vertex) - 1);
        if (numEdgesForTreeVertex.get(vertex) == 0) {
            numEdgesForTreeVertex.remove(vertex);
        }
    }
}

class GameRunner {
    List<List<Integer>> edges;
    GameGraph initialGraph;
    String memoFile;
    Map<String, Integer> memo;
    Map<String, Integer> progress;

    GameRunner(List<List<Integer>> edges) {
        this.edges = edges;
        this.initialGraph = new GameGraph(edges);
        this.memoFile = "net_scores.txt";
        this.progress = new HashMap<>();
        progress.put("top_level", initialGraph.numEdges);
        progress.put("count", 0);
    }

    void run(boolean writeFile) {
        initMemo();
        int netScore = netScore(initialGraph, 0);
        if (netScore == 0) {
            System.out.println("Tie game.");
            System.out.flush();
        } else {
            String winner = netScore > 0 ? "P1" : "P2";
            int firstPlayerScore = (initialGraph.numVertices + netScore) / 2;
            int secondPlayerScore = (initialGraph.numVertices - netScore) / 2;
            System.out.printf("%s wins with a score of (%d - %d)%n", winner, firstPlayerScore, secondPlayerScore);
            System.out.flush();
        }
        if (writeFile) {
            writeMemo();
        }
    }

    void initMemo() {
        // Create a new empty file or truncate the existing file
        try {
            new FileWriter(memoFile, false).close();
        } catch (IOException e) {
            System.out.println("Error clearing memo file: " + e.getMessage());
        }
    
        memo = new HashMap<>();
        try (Scanner scanner = new Scanner(new java.io.File(memoFile))) {
            while (scanner.hasNextLine()) {
                String[] items = scanner.nextLine().split(",");
                memo.put(items[0], Integer.parseInt(items[1]));
            }
        } catch (Exception e) {
            System.out.println("Error reading memo file: " + e.getMessage());
        }
    }

    void writeMemo() {
        try (java.io.FileWriter fileWriter = new java.io.FileWriter(memoFile)) {
            for (Map.Entry<String, Integer> entry : memo.entrySet()) {
                fileWriter.write(entry.getKey() + "," + entry.getValue() + "\n");
            }
        } catch (Exception e) {
            System.out.println("Error writing memo file: " + e.getMessage());
        }
    }

    int netScore(GameGraph graph, int depth) {
        if (memo.containsKey(graph.getKey())) {
            return memo.get(graph.getKey());
        }
        if (graph.isTree()) {
            memo.put(graph.getKey(), graph.numVertices);
            return graph.numVertices;
        }
        int newDepth = depth + 1;
        int bestOutcome = -1 * graph.numVertices;
        List<List<Integer>> triedEdges = new ArrayList<>();
        for (List<Integer> edge : graph.edges) {
            if (triedEdges.contains(edge)) {
                continue;
            }
            triedEdges.add(edge);
            GameGraph newGraph;
            int points;
            newGraph = new GameGraph(new ArrayList<>(graph.edges));
            newGraph.edges.remove(edge);
            points = 0;
            if (!newGraph.containsVertex(edge.get(0))) {
                points++;
            }
            if (edge.get(1) != edge.get(0)) {
                if (!newGraph.containsVertex(edge.get(1))) {
                    points++;
                }
            }
            int mult = points > 0 ? 1 : -1;
            int outcome = points + mult * netScore(newGraph, newDepth);
            if (outcome > bestOutcome) {
                bestOutcome = outcome;
                if (outcome == graph.numVertices) {
                    break;
                }
            }
        }
        trackProgress(depth);
        memo.put(graph.getKey(), bestOutcome);
        return bestOutcome;
    }

    void trackProgress(int depth) {
        if (depth <= progress.get("top_level")) {
            if (depth == progress.get("top_level")) {
                progress.put("count", progress.get("count") + 1);
            } else {
                progress.put("top_level", depth);
                progress.put("count", 1);
            }
            long elapsedMillis = System.currentTimeMillis() - algorithm.startTime;
            double elapsedSecs = elapsedMillis / 1000.0;
            System.out.printf("top solved depth:%d count:%d seconds:%.3f%n", depth, progress.get("count"), elapsedSecs);
            System.out.flush();
        }
    }
}

public class algorithm {
    public static long startTime;

    public static void main(String[] args) {
        startTime = System.currentTimeMillis();
        List<List<Integer>> edges;

        if (args.length >= 2) {
            String graphType = args[0];
            int numVertices = Integer.parseInt(args[1]);
            edges = generateGraph(graphType, numVertices);
        } else {
            edges = getEdgesFromInputFile();
        }

        new GameRunner(edges).run(true);
    }

    static List<List<Integer>> generateGraph(String type, int numVertices) {
        List<List<Integer>> edges = new ArrayList<>();
        if ("complete".equals(type)) {
            for (int i = 0; i < numVertices; i++) {
                for (int j = i + 1; j < numVertices; j++) {
                    edges.add(List.of(i, j));
                }
            }
        } else if ("wheel".equals(type)) {
            for (int i = 0; i < numVertices - 1; i++) {
                edges.add(List.of(i, i + 1));
                edges.add(List.of(i, numVertices - 1));
            }
            edges.add(List.of(numVertices - 1, 0));
        } else {
            System.err.println("Invalid graph type. Use 'complete' or 'wheel'.");
        }
        return edges;
    }

    static List<List<Integer>> getEdgesFromInputFile() {
        List<List<Integer>> edges = new ArrayList<>();
        try (Scanner scanner = new Scanner(new java.io.File("game_input.txt"))) {
            while (scanner.hasNextLine()) {
                String[] vertices = scanner.nextLine().split(",");
                edges.add(List.of(Integer.parseInt(vertices[0]), Integer.parseInt(vertices[1])));
            }
        } catch (Exception e) {
            System.out.println("Error reading input file: " + e.getMessage());
        }
        return edges;
    }
}