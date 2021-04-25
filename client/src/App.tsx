import * as React from "react"
import {
  ChakraProvider,
  theme,
} from "@chakra-ui/react"
import {
  BrowserRouter as Router,
  Switch,
  Route,
} from 'react-router-dom';
import NavBar from './components/NavBar'
import LoginPage from "./pages/LoginPage";
import ForgetPasswordPage from "./pages/ForgetPasswordPage";
import SignupPage from "./pages/SignupPage";
import LearnPage from "./pages/LearnPage";
import InventoryPage from "./pages/InventoryPage";
import StatsPage from './pages/StatsPage';
import { ColorModeSwitcher } from './ColorModeSwitcher';

export const App = () => (
  <ChakraProvider theme={theme}>
    <Router>
      <Switch>
        <Route>
          <ColorModeSwitcher  float="right"/>
          <Route exact path="/login">
            <LoginPage />
          </Route>
          <Route exact path="/signup">
            <SignupPage />
          </Route>
          <Route exact path="/forgot">
            <ForgetPasswordPage />
          </Route>
        </Route>
        <Route>
          <NavBar />
          <Route exact path="/">
            <LearnPage />
          </Route>
          <Route exact path="/inventory">
            <InventoryPage />
          </Route>
          <Route exact path="/stats">
            <StatsPage />
          </Route>
        </Route>
      </Switch>
    </Router>
  </ChakraProvider>
)
