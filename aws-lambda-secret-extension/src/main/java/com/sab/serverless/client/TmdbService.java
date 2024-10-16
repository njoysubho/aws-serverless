package com.sab.serverless.client;

import com.sab.serverless.secret.SecretManager;
import info.movito.themoviedbapi.TmdbApi;
import info.movito.themoviedbapi.model.MovieDb;
import info.movito.themoviedbapi.model.core.MovieResultsPage;

import java.io.IOException;
import java.util.List;
import java.util.stream.Collectors;


public class TmdbService{

    private final SecretManager secretManager;
    private final TmdbApi tmdbApi;

    public TmdbService(){
        this.secretManager = new SecretManager();
        String secret = System.getenv("TMDB_API_KEY");
        System.out.println("SecretId: " + secret);
        String key = secretManager.getSecret(secret);
        this.tmdbApi = new TmdbApi(key);
    }
    public List<String> getMovies() {
        MovieResultsPage results  = tmdbApi.getMovies().getPopularMovies("en", 1);
        return results.getResults()
                .stream()
                .map(MovieDb::getTitle)
                .collect(Collectors.toList());
    }
}
