import React from 'react';
import { Redirect } from 'react-router-dom';
import { Route } from 'react-router-dom';

interface ProtectedRouteProps {
    Component: React.FC;
    path: string;
    isAuthenticated: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ Component, path, isAuthenticated }) => {
    return (
        <Route
            exact
            path={path}
            render={() => (
                isAuthenticated ? (
                    <Component />
                ) : (
                    <Redirect to="/login"/>
                )
            )}
        />
    )
}

export default ProtectedRoute;